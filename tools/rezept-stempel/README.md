# Rezept-Stempel

Browser-App zum Stempeln von Rezept-PDFs. Ein Klick setzt `- (x)g DD.MM.YYYY` (Europe/Berlin), das Mausrad ändert die Menge, Speichern schreibt **eine neue Datei**. Das Original bleibt unangetastet.

Alles läuft lokal im Browser. Es gibt keinen Server-Upload.

## Starten

```bash
cd tools/rezept-stempel/web
npm install
npm run dev
```

Dann `http://127.0.0.1:43174` öffnen (Port ist fest, nicht 3000/5173/8080).

Tests: `npm test`  
Production-Build: `npm run build` und `npm run preview`

## Bedienung

| Aktion | Wirkung |
| --- | --- |
| **PDF öffnen** oder Dateien auf die Seite ziehen | Eine oder mehrere PDFs. In Chrome merkt sich die App den Datei-Handle. |
| **Beispiel öffnen** | Lädt `public/samples/TEST-REZEPT-0001.pdf` (nur TEST-Kennungen). |
| **Klick aufs Rezept** | Setzt den Stempel. In den drei Verordnungszeilen eines A4-Kassenrezepts rastet die Position ein. |
| **Mausrad** / **−5 / +5** | Menge 5–100 g in 5er-Schritten. Der letzte Stempel wird mitgezogen. |
| **Erste Rp-Zeile** / Enter | Standardposition auf der ersten Verordnungszeile. |
| **Speichern** / Strg+S | Neue Datei `Originalname_YYYY-MM-DD_HHMM.pdf`. Original nie überschreiben. |
| **Letzten Stempel entfernen** / Strg+Z | Nimmt den letzten Overlay zurück. |

## Speichern

- **Chrome / Edge**, wenn die Datei über den Dateidialog oder per Drop mit Datei-Handle geöffnet wurde: File System Access API, `showSaveFilePicker` mit `startIn` am Original-Handle. Der Dialog landet typischerweise **neben der Quelldatei**. Vorgeschlagener Name enthält den Timestamp. Wählt man denselben Namen wie das Original, bricht die App ab.
- **Sonst** (Firefox, Safari, Beispiel-PDF, Drop ohne Handle): Download von `Originalname_YYYY-MM-DD_HHMM.pdf`. Datei im Download-Ordner bzw. im Dialog neben dem Original ablegen — nicht die Quelle überschreiben.

Stempeltext: `- 25g 29.09.2026` (Beispiel), 11 pt fett, weißer Untergrund.

## Musterdatei

`web/public/samples/TEST-REZEPT-0001.pdf` und `samples/TEST-REZEPT-0001.pdf` enthalten nur TEST-Kennungen. Keine realen Patientendaten.
