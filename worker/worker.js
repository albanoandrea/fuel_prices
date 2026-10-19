// Fa da tramite verso il MIMIT, che blocca GitHub Actions e non permette
// le chiamate dal browser (niente CORS). Accetta solo questi indirizzi:
//   /prezzi?ids=53735,51142   prezzi in tempo reale di alcuni benzinai (per l'app)
//   /csv/prezzi               prezzo_alle_8.csv (per il workflow)
//   /csv/anagrafica           anagrafica_impianti_attivi.csv (per il workflow)

const ORIGINI = ["https://albanoandrea.github.io", "http://localhost:8000"];
const URL_LIVE = "https://carburanti.mise.gov.it/ospzApi/registry/servicearea/";
const CSV = {
  "/csv/prezzi": "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv",
  "/csv/anagrafica": "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv",
};
const MAX_IDS = 40;
const HEADERS_MIMIT = { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) prezzi-benzina/1.0" };

function cors(req) {
  const o = req.headers.get("Origin");
  return o && ORIGINI.includes(o) ? { "Access-Control-Allow-Origin": o, Vary: "Origin" } : {};
}

function risposta(req, corpo, status = 200, extra = {}) {
  return new Response(corpo, { status, headers: { ...cors(req), ...extra } });
}

// Un benzinaio: solo i prezzi, null se il MIMIT non risponde.
async function live(id) {
  try {
    const r = await fetch(URL_LIVE + id, {
      headers: HEADERS_MIMIT,
      cf: { cacheTtl: 300, cacheEverything: true },
      signal: AbortSignal.timeout(15000),
    });
    if (!r.ok) return null;
    const d = await r.json();
    return (d.fuels || []).map((f) => ({ name: f.name, isSelf: f.isSelf, price: f.price, insertDate: f.insertDate }));
  } catch (e) {
    return null;
  }
}

export default {
  async fetch(req) {
    if (req.method === "OPTIONS") return risposta(req, null, 204, { "Access-Control-Allow-Methods": "GET" });
    if (req.method !== "GET") return risposta(req, "Solo GET", 405);
    const url = new URL(req.url);

    if (url.pathname === "/prezzi") {
      const ids = [...new Set((url.searchParams.get("ids") || "").split(",").filter((x) => /^\d{1,7}$/.test(x)))];
      if (!ids.length || ids.length > MAX_IDS) return risposta(req, `Da 1 a ${MAX_IDS} codici in ids`, 400);
      const prezzi = await Promise.all(ids.map(live));
      const out = {};
      ids.forEach((id, i) => { if (prezzi[i]) out[id] = prezzi[i]; });
      return risposta(req, JSON.stringify(out), 200, {
        "Content-Type": "application/json",
        "Cache-Control": "max-age=120",
      });
    }

    if (CSV[url.pathname]) {
      const r = await fetch(CSV[url.pathname], { headers: HEADERS_MIMIT, cf: { cacheTtl: 600, cacheEverything: true } });
      return risposta(req, r.body, r.status, { "Content-Type": "text/csv" });
    }

    return risposta(req, "Non trovato", 404);
  },
};
