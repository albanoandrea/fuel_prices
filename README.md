# I miei benzinai

App per il telefono che mostra l'ultimo prezzo conosciuto dei tuoi benzinai preferiti.
I dati sono quelli ufficiali del MIMIT (open data, licenza IODL 2.0), aggiornati ogni giorno in automatico da GitHub Actions.

## Comandi

Dalla cartella del progetto:

```sh
# Aggiorna i prezzi da questo PC e pubblica la pagina (quando il MIMIT blocca GitHub Actions)
python scripts/aggiorna_a_mano.py

# Aggiorna solo data.json in locale, senza commit né push (per provare)
python scripts/aggiorna.py

# Fa partire subito il workflow su GitHub
gh workflow run aggiorna.yml

# Ultimi run del workflow
gh run list -L 5

# Dettaglio di un run con gli avvisi (chiede quale run scegliere)
gh run view
```

## Come funziona

- `scripts/aggiorna.py` scarica i CSV del MIMIT e crea `data.json` con i benzinai delle province in `config.json`.
- `scripts/aggiorna_a_mano.py` fa lo stesso da questo PC, poi commit e push: serve quando il MIMIT non risponde a GitHub Actions.
- In `config.json`, `live` elenca i codici MIMIT dei benzinai da aggiornare anche in tempo reale (servizio Osservaprezzi, non ufficiale come open data).
- `.github/workflows/aggiorna.yml` esegue lo script quattro volte al giorno (8:30, 9:30, 12:00 e 17:30) e pubblica il sito su GitHub Pages.
- `index.html` è l'app: scegli i benzinai con la stella, restano salvati sul telefono.
- `worker/` è un Worker Cloudflare che fa da tramite verso il MIMIT, che blocca GitHub Actions e non accetta chiamate dal browser. Se in `config.json` c'è `proxy`, lo usano sia lo script (per CSV e prezzi live) sia l'app, che a ogni apertura chiede i prezzi in tempo reale dei tuoi preferiti. Se il Worker non risponde, lo script prova direttamente il MIMIT e l'app mostra i prezzi di `data.json`.

## Worker Cloudflare

Il Worker è online all'indirizzo **https://benzinai.albano-andrea.workers.dev** (account Cloudflare gratuito, Worker `benzinai`), già scritto in `config.json` alla voce `proxy`.

Per provarlo:

- [/prezzi?ids=53735](https://benzinai.albano-andrea.workers.dev/prezzi?ids=53735): prezzi in tempo reale in JSON.
- [/csv/prezzi](https://benzinai.albano-andrea.workers.dev/csv/prezzi) e [/csv/anagrafica](https://benzinai.albano-andrea.workers.dev/csv/anagrafica): i CSV del MIMIT (circa 4 MB l'uno).

Se `/prezzi` restituisce `{}`, o le pagine non finiscono di caricare, il MIMIT ha bloccato anche Cloudflare. L'app mostra i prezzi di `data.json` e lo script prova il MIMIT diretto.

### Aggiornare il codice del Worker

Il codice su Cloudflare non si aggiorna da solo quando cambia `worker/worker.js`:

1. Su [dash.cloudflare.com](https://dash.cloudflare.com): **Compute (Workers)** → **Workers & Pages** → `benzinai`.
2. **Edit code**: sostituisci tutto con il contenuto di `worker/worker.js` e premi **Deploy**.

In alternativa, con Node installato: `cd worker` e poi `npx wrangler deploy`.

Se il sito cambia indirizzo, aggiorna `ORIGINI` in `worker/worker.js`. Per provare l'app in locale usa `python -m http.server 8000`.
