# Rezept-Stempel

Lokales Desktop-Werkzeug für die Apotheke: ein Rezept-PDF öffnen, mit einem Klick `- (x)g TT.MM.JJJJ` setzen, mit dem Mausrad die Menge von 5–100 g in 5er-Schritten ändern und die gestempelte Datei **direkt neben das Original** schreiben.

Kein Browser, kein Download-Dialog. Speichern legt eine neue PDF im Quellordner ab.

## Voraussetzungen

- Python 3.12+
- `python3-tk` (Debian/Ubuntu: `sudo apt install python3-tk`)
- Anzeige (Desktop-Sitzung)

## Start

```bash
cd tools/rezept-stempel
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m rezept_stempel
```

Oder nach der Installation: `rezept-stempel`.

Beim Start eine Datei öffnen:

```bash
python -m rezept_stempel --open samples/TEST-REZEPT-0001.pdf
```

## Bedienung

| Aktion | Wirkung |
| --- | --- |
| **PDF öffnen** | Wählt das Rezept. |
| **Beispiel öffnen** | Lädt `samples/TEST-REZEPT-0001.pdf` (nur TEST-Kennungen). |
| **Klick** | Setzt `- 25g 29.09.2026` (Menge und Berlin-Datum). In den drei Rp-Zeilen rastet der Stempel ein. Weißer Untergrund, 11 pt fett. |
| **Mausrad** | Ändert `(x)` in 5er-Schritten, 5–100 g. Der zuletzt gesetzte Stempel wird mitgezogen. |
| **Erste Rp-Zeile** / Enter | Standardposition: erste Verordnungszeile, nach dem Präparatenamen. |
| **Speichern** | Schreibt `Originalname_YYYY-MM-DD_HHMM.pdf` in denselben Ordner wie die Quelle. Das Original bleibt unverändert. |
| **Letzten Stempel entfernen** / Strg+Z | Nimmt den letzten Overlay zurück. |

Datum auf dem Stempel: `DD.MM.YYYY` in `Europe/Berlin`.  
Dateiname: `YYYY-MM-DD_HHMM`, bei Kollision `…-2.pdf`.

## Musterdatei

`samples/TEST-REZEPT-0001.pdf` ist ein synthetisches A4-Kassenrezept (`TEST-PATIENT-0001`, `TEST-PREPARAT`, …). Keine realen Patientendaten.

Neu erzeugen:

```bash
python -m rezept_stempel.sample_pdf
```

## Tests

```bash
cd tools/rezept-stempel
source .venv/bin/activate
pytest
```

Die Tests prüfen Mengenstufen, Berlin-Datum, den Dateinamen neben der Quelle und dass Speichern die Originaldatei nicht überschreibt.
