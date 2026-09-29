# Rezept-Stempel

Lokales Desktop-Werkzeug für die Apotheke: Rezept-PDFs per **Drag & Drop** oder Doppelklick öffnen, mit einem Klick `- (x)g TT.MM.JJJJ` setzen, mit dem Mausrad die Menge von 5–100 g in 5er-Schritten ändern und die gestempelte Datei **direkt neben das Original** schreiben.

Kein Browser, kein Download-Dialog, kein Terminal im Alltag.

## Windows: ohne Terminal starten

Einmal einrichten (PowerShell im Ordner `tools\rezept-stempel`):

```powershell
.\packaging\windows\build.ps1
```

Das erzeugt `dist\Rezept-Stempel.exe` (kein Konsolenfenster) und legt Verknüpfungen **Desktop** und **Startmenü** `Rezept-Stempel` an.

Danach:

1. Doppelklick auf **Rezept-Stempel** (Desktop oder Startmenü)
2. PDFs auf das Fenster **oder** auf die Verknüpfung / EXE ziehen
3. Stempeln, Speichern

Nur Verknüpfung (falls die EXE schon da ist, oder mit `pythonw`):

```powershell
.\packaging\windows\install-shortcut.ps1
```

Ohne PowerShell: `packaging\windows\install-shortcut.vbs` doppelklicken.

Ohne Build, wenn Python installiert ist: `Rezept-Stempel.pyw` doppelklicken (`pythonw`, keine Konsole).

PDFs auf die Verknüpfung oder EXE legen öffnet sie direkt (Windows übergibt die Pfade als Startargumente).

## Drag & Drop

- Eine oder mehrere PDFs auf das Fenster ziehen — sie erscheinen unter **Offene Dateien**
- Ordner: nur PDFs in der ersten Ebene, keine Unterordner
- Weitere Drops fügen Dateien hinzu; Stempel je Datei getrennt
- Speichern gilt immer für die **aktuelle** Datei und schreibt neben deren Original

## Bedienung

| Aktion | Wirkung |
| --- | --- |
| **PDF öffnen** | Eine oder mehrere Dateien wählen. |
| **Drag & Drop** | PDFs auf Fenster oder Verknüpfung. |
| **Beispiel öffnen** | Lädt `samples/TEST-REZEPT-0001.pdf` (nur TEST-Kennungen). |
| **Klick** | Setzt `- 25g 29.09.2026`. In den drei Rp-Zeilen rastet der Stempel ein. Weißer Untergrund, 11 pt fett. |
| **Mausrad** | `(x)` in 5er-Schritten, 5–100 g. Der letzte Stempel wird mitgezogen. |
| **Erste Rp-Zeile** / Enter | Standardposition: erste Verordnungszeile. |
| **Speichern** | `Originalname_YYYY-MM-DD_HHMM.pdf` im **selben Ordner** wie die Quelle. Original unverändert. |
| **Letzten Stempel entfernen** / Strg+Z | Nimmt den letzten Overlay zurück. |

Datum auf dem Stempel: `DD.MM.YYYY` in `Europe/Berlin`.  
Dateiname: `YYYY-MM-DD_HHMM`, bei Kollision `…-2.pdf`.

## Entwicklung (mit Terminal)

```bash
cd tools/rezept-stempel
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,desktop]"
python -m rezept_stempel
```

```bash
python -m rezept_stempel --open samples/TEST-REZEPT-0001.pdf
pytest
```

Debian/Ubuntu zusätzlich: `sudo apt install python3-tk`.

## Musterdatei

`samples/TEST-REZEPT-0001.pdf` ist ein synthetisches A4-Kassenrezept (`TEST-PATIENT-0001`, `TEST-PREPARAT`, …). Keine realen Patientendaten.
