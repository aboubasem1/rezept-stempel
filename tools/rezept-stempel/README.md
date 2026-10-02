# Rezept-Stempel

Stempelt Rezept-PDFs im Browser: `- (x)g DD.MM.YYYY` (Europe/Berlin). Mausrad ändert die Menge (5–100 g, 5er-Schritte) **nur am ausgewählten Stempel**. Rechte Maustaste länger als 1 s: freie Menge ohne 5er-Rundung. Klicks in den Verordnungszeilen rasten ein. Speichern schreibt `Originalname_YYYY-MM-DD_HHMM.pdf` — das Original bleibt.

PDFs bleiben im Browser. Nichts wird hochgeladen.

## Entwicklung

```bash
cd tools/rezept-stempel/web
npm install
npm run dev
npm run build
npm test
```

## Production

GitHub → Vercel auto-deploy. `main` ist Production, andere Branches sind Previews.

- Repo: https://github.com/aboubasem1/rezept-stempel
- Live: https://rezept-stempel.vercel.app
- Vercel-Projekt: Root Directory `tools/rezept-stempel/web`, Framework Vite, Output `dist`. Keine Env-Vars, keine Serverless Functions.

## Windows: PDF statt Adobe hier öffnen

Ein Browser-Tab kann Adobe nicht ersetzen. Nur die installierte App.

1. In **Microsoft Edge** oder **Chrome** https://rezept-stempel.vercel.app öffnen.
2. App installieren: Edge `⋯` → Apps → Diese Website als App installieren. Chrome: Installieren-Symbol in der Adressleiste oder `⋮` → Rezept-Stempel installieren.
3. Windows: **Einstellungen → Apps → Standard-Apps**.
4. `.pdf` suchen und **Rezept-Stempel** statt Adobe Reader/Acrobat setzen.

Danach öffnet ein Doppelklick auf ein Rezept-PDF die Stempel-Oberfläche. Firefox unterstützt das nicht zuverlässig. Ohne installierte App bleibt Adobe der Standard.
