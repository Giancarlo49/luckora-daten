# luckora-daten

Ziehungsdaten für die App **Luckora** (6 aus 49 und 5 aus 50, ab 2018).

- `daten/6aus49.csv` – `datum,z1..z6,superzahl`
- `daten/5aus50.csv` – `datum,z1..z5,e1,e2`

Eine GitHub Action (`.github/workflows/aktualisieren.yml`) holt die Daten
zweimal täglich aus [dev-baris/lottery-archive](https://github.com/dev-baris/lottery-archive),
prüft sie (Zahlenbereiche, Wochentage, keine Doppelten, nie weniger als vorher)
und speichert sie nur bei Änderungen. Schlägt die Prüfung fehl, bleiben die
alten Daten stehen und GitHub schickt eine E-Mail.

Quelle wechseln: in `aktualisieren.py` die Zeile `QUELLE` bzw. die Pfade anpassen.

Alle Angaben ohne Gewähr.
