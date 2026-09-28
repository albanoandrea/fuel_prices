"""
Scarica i prezzi carburanti dal MIMIT (open data) e crea data.json
con i distributori delle province scelte in config.json.

Se un distributore non compare nel file di oggi, resta l'ultimo prezzo
conosciuto (preso dal data.json precedente).

Per i distributori elencati in "live" (config.json) chiede anche i prezzi
in tempo reale al servizio Osservaprezzi del MIMIT. Vince sempre il prezzo
con la data di comunicazione più recente.
"""

import csv
import io
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

URL_PREZZI = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"
URL_ANAGRAFICA = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
URL_LIVE = "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/{}"

try:
    ROMA = ZoneInfo("Europe/Rome")
except Exception:  # noqa: BLE001
    ROMA = timezone.utc
MAI = datetime.min

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "config.json"
OUTPUT = ROOT / "data.json"


def scarica(url, tentativi=4):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) prezzi-benzina/1.0",
        "Accept": "text/csv,*/*",
    }
    for n in range(1, tentativi + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as r:
                raw = r.read()
            for enc in ("utf-8-sig", "cp1252", "latin-1"):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
        except Exception as e:  # noqa: BLE001
            print(f"Errore download {url} (tentativo {n}): {e}", file=sys.stderr)
            time.sleep(10 * n)
    raise RuntimeError(f"Impossibile scaricare {url}")


def leggi_csv(testo):
    """Restituisce (data_estrazione, righe come dict con chiavi minuscole)."""
    righe = testo.splitlines()
    estrazione = ""
    if righe and righe[0].lower().startswith("estrazione"):
        estrazione = righe[0].split("del", 1)[-1].strip(" |;,")
        righe = righe[1:]
    if not righe:
        return estrazione, []
    intestazione = righe[0]
    sep = "|" if "|" in intestazione else (";" if ";" in intestazione else ",")
    reader = csv.reader(io.StringIO("\n".join(righe)), delimiter=sep, quoting=csv.QUOTE_NONE)
    header = [h.strip().lower() for h in next(reader)]
    out = []
    for row in reader:
        if len(row) < len(header):
            continue
        out.append({header[i]: row[i].strip() for i in range(len(header))})
    return estrazione, out


def num(x):
    try:
        return float(x.replace(",", "."))
    except (ValueError, AttributeError):
        return None


def data_d(s):
    """Data di comunicazione "gg/mm/aaaa hh:mm:ss" (ora italiana)."""
    try:
        return datetime.strptime(s.strip(), "%d/%m/%Y %H:%M:%S")
    except (ValueError, AttributeError):
        return None


def aggiorna_prezzo(prezzi, chiave, prezzo, d):
    """Salva il prezzo, a meno che quello che c'è già sia più recente."""
    vecchio = prezzi.get(chiave, {})
    if (data_d(vecchio.get("d")) or MAI) > (data_d(d) or MAI):
        return False
    nuovo = {"p": prezzo, "d": d}
    if vecchio.get("p") is not None and vecchio["p"] != prezzo:
        nuovo["pp"] = vecchio["p"]
    elif "pp" in vecchio:
        nuovo["pp"] = vecchio["pp"]
    prezzi[chiave] = nuovo
    return True


def aggiorna_live(impianti, ids):
    """Prezzi in tempo reale per pochi distributori. Se non risponde, si va avanti."""
    aggiornati = 0
    for iid in ids:
        if iid not in impianti:
            print(f"Live: {iid} non è nelle province di config.json", file=sys.stderr)
            continue
        try:
            dati = json.loads(scarica(URL_LIVE.format(iid), tentativi=2))
        except Exception as e:  # noqa: BLE001
            print(f"Live: impossibile leggere {iid}: {e}", file=sys.stderr)
            continue
        for f in dati.get("fuels", []):
            prezzo = f.get("price")
            if not isinstance(prezzo, (int, float)) or not f.get("insertDate"):
                continue
            quando = datetime.fromisoformat(f["insertDate"].replace("Z", "+00:00"))
            d = quando.astimezone(ROMA).strftime("%d/%m/%Y %H:%M:%S")
            chiave = f"{f.get('name', '')}|{'1' if f.get('isSelf') else '0'}"
            if aggiorna_prezzo(impianti[iid]["prezzi"], chiave, float(prezzo), d):
                aggiornati += 1
        time.sleep(0.5)
    return aggiornati


def main():
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    province = {p.strip().upper() for p in config.get("province", []) if p.strip()}
    if not province:
        sys.exit("Nessuna provincia in config.json")

    vecchi = {}
    if OUTPUT.exists():
        try:
            vecchi = json.loads(OUTPUT.read_text(encoding="utf-8")).get("impianti", {})
        except Exception:  # noqa: BLE001
            vecchi = {}

    _, anagrafica = leggi_csv(scarica(URL_ANAGRAFICA))
    estrazione, prezzi = leggi_csv(scarica(URL_PREZZI))
    print(f"Anagrafica: {len(anagrafica)} righe, prezzi: {len(prezzi)} righe")

    impianti = {}
    for a in anagrafica:
        prov = a.get("provincia", "").upper()
        if prov not in province:
            continue
        iid = a.get("idimpianto")
        if not iid:
            continue
        impianti[iid] = {
            "n": a.get("nome impianto", ""),
            "b": a.get("bandiera", ""),
            "g": a.get("gestore", ""),
            "i": a.get("indirizzo", ""),
            "c": a.get("comune", ""),
            "pr": prov,
            "lat": num(a.get("latitudine", "")),
            "lon": num(a.get("longitudine", "")),
            "prezzi": dict(vecchi.get(iid, {}).get("prezzi", {})),
        }

    # Distributori che erano nel file vecchio ma oggi mancano: li teniamo.
    for iid, v in vecchi.items():
        if iid not in impianti and v.get("pr") in province:
            impianti[iid] = v

    aggiornati = 0
    for p in prezzi:
        iid = p.get("idimpianto")
        if iid not in impianti:
            continue
        prezzo = num(p.get("prezzo", ""))
        if prezzo is None:
            continue
        chiave = f"{p.get('desccarburante', '')}|{p.get('isself', '')}"
        if aggiorna_prezzo(impianti[iid]["prezzi"], chiave, prezzo, p.get("dtcomu", "")):
            aggiornati += 1

    live = [str(x).strip() for x in config.get("live", []) if str(x).strip()]
    live_aggiornati = aggiorna_live(impianti, live) if live else 0

    dati = {
        "aggiornato": datetime.now(timezone.utc).isoformat(timespec="minutes"),
        "estrazione": estrazione,
        "province": sorted(province),
        "impianti": impianti,
    }
    OUTPUT.write_text(json.dumps(dati, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Salvati {len(impianti)} distributori, {aggiornati} prezzi aggiornati, "
          f"{live_aggiornati} prezzi in tempo reale per {len(live)} distributori")


if __name__ == "__main__":
    main()
