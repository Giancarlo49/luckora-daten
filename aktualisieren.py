"""Holt die aktuellen Ziehungen, prüft sie und schreibt sie nach daten/.

Läuft automatisch per GitHub Action (siehe .github/workflows/).
Bricht mit Fehler ab (Datei bleibt dann unverändert), wenn die Quelle
fehlt, kaputt ist oder weniger Ziehungen liefert als bisher.
"""

import csv
import io
import sys
import urllib.request
from datetime import date, timedelta
from pathlib import Path

QUELLE = "https://raw.githubusercontent.com/dev-baris/lottery-archive/main/"
AB = date(2018, 1, 1)  # gleicher Zeitraum wie die in der App eingebauten Daten
ZIEL = Path(__file__).parent / "daten"

SPIELE = {
    # Datei: (Quellpfad, Anzahl Zahlen, Max, Anzahl Zusatz, Zusatz-Min, Zusatz-Max-Funktion, Wochentage-Funktion)
    "6aus49.csv": dict(
        pfad="de/lotto_6aus49/results.csv",
        kopf="datum,z1,z2,z3,z4,z5,z6,superzahl",
        anzahl=6, maximum=49, zusatz=1, zmin=0,
        zmax=lambda d: 9,
        tage=lambda d: {2, 5},  # Mi, Sa
    ),
    "5aus50.csv": dict(
        pfad="eu/eurojackpot/results.csv",
        kopf="datum,z1,z2,z3,z4,z5,e1,e2",
        anzahl=5, maximum=50, zusatz=2, zmin=1,
        zmax=lambda d: 12 if d >= date(2022, 3, 25) else 10,
        tage=lambda d: {1, 4} if d >= date(2022, 3, 25) else {4},  # (Di,) Fr
    ),
}


def lade(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8")


def pruefe_und_wandle(text: str, s: dict) -> list[str]:
    zeilen = []
    letztes = None
    heute = date.today()
    for nr, z in enumerate(csv.reader(io.StringIO(text))):
        if nr == 0:
            continue  # Kopfzeile
        if not z:
            continue
        d = date.fromisoformat(z[0])
        if d < AB:
            continue
        if d > heute + timedelta(days=1):
            raise ValueError(f"Datum in der Zukunft: {d}")
        if letztes and d <= letztes:
            raise ValueError(f"Reihenfolge/Doppelt: {d}")
        if d.weekday() not in s["tage"](d):
            raise ValueError(f"Unerwarteter Wochentag: {d}")
        werte = [int(x) for x in z[1:]]
        if len(werte) != s["anzahl"] + s["zusatz"]:
            raise ValueError(f"Falsche Spaltenzahl: {z}")
        zahlen, zusatz = werte[: s["anzahl"]], werte[s["anzahl"] :]
        if len(set(zahlen)) != len(zahlen) or not all(1 <= x <= s["maximum"] for x in zahlen):
            raise ValueError(f"Ungültige Zahlen: {z}")
        if len(set(zusatz)) != len(zusatz) or not all(s["zmin"] <= x <= s["zmax"](d) for x in zusatz):
            raise ValueError(f"Ungültige Zusatzzahlen: {z}")
        zeilen.append(",".join([d.isoformat(), *map(str, werte)]))
        letztes = d
    return zeilen


def main() -> int:
    ZIEL.mkdir(exist_ok=True)
    fehler = False
    for datei, s in SPIELE.items():
        ziel = ZIEL / datei
        try:
            neu = pruefe_und_wandle(lade(QUELLE + s["pfad"]), s)
            alt = ziel.read_text().splitlines()[1:] if ziel.exists() else []
            if len(neu) < len(alt):
                raise ValueError(f"Quelle hat weniger Ziehungen ({len(neu)}) als bisher ({len(alt)})")
            if len(neu) < 300:
                raise ValueError(f"Zu wenige Ziehungen: {len(neu)}")
            ziel.write_text("\n".join([s["kopf"], *neu]) + "\n")
            print(f"{datei}: {len(neu)} Ziehungen, letzte {neu[-1]}")
        except Exception as e:  # noqa: BLE001
            print(f"FEHLER {datei}: {e}", file=sys.stderr)
            fehler = True
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
