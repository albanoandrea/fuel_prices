# I miei benzinai

App per il telefono che mostra l'ultimo prezzo conosciuto dei tuoi benzinai preferiti.
I dati sono quelli ufficiali del MIMIT (open data, licenza IODL 2.0), aggiornati ogni giorno in automatico da GitHub Actions.

- `scripts/aggiorna.py` scarica i CSV del MIMIT e crea `data.json` con i benzinai delle province in `config.json`.
- In `config.json`, `live` elenca i codici MIMIT dei benzinai da aggiornare anche in tempo reale (servizio Osservaprezzi, non ufficiale come open data).
- `.github/workflows/aggiorna.yml` esegue lo script ogni giorno e pubblica il sito su GitHub Pages.
- `index.html` è l'app: scegli i benzinai con la stella, restano salvati sul telefono.
