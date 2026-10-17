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
- `.github/workflows/aggiorna.yml` esegue lo script ogni ora (dalle 7:30 alle 21:30) e pubblica il sito su GitHub Pages.
- `index.html` è l'app: scegli i benzinai con la stella, restano salvati sul telefono.
