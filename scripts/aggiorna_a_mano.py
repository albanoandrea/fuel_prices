"""
Aggiorna i prezzi da questo PC e li pubblica (per quando il MIMIT blocca GitHub Actions).

    python scripts/aggiorna_a_mano.py

Scarica l'ultima versione da GitHub, lancia aggiorna.py, fa il commit di
data.json e il push. Il push fa partire il workflow, che vede il messaggio
"Prezzi aggiornati a mano" e pubblica la pagina senza riscaricare i prezzi.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(*args):
    subprocess.run(["git", *args], cwd=ROOT, check=True)


def main():
    git("pull", "--rebase", "--autostash", "origin", "master")
    subprocess.run([sys.executable, str(ROOT / "scripts" / "aggiorna.py")], cwd=ROOT, check=True)
    git("add", "data.json")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
        print("Nessun prezzo cambiato, niente da pubblicare")
        return
    git("commit", "-m", f"Prezzi aggiornati a mano {datetime.now():%Y-%m-%d %H:%M}")
    git("push", "origin", "HEAD:master")
    print("Pubblicato: la pagina si aggiorna appena finisce il workflow su GitHub")


if __name__ == "__main__":
    main()
