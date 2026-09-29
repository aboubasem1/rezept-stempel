# Rezept-Stempel

Stempelt Rezept-PDFs im Browser: `- (x)g DD.MM.YYYY` (Europe/Berlin). Mausrad ändert die Menge (5–100 g, 5er-Schritte) **nur am ausgewählten Stempel**. Klicks in den Verordnungszeilen rasten ein. Speichern schreibt `Originalname_YYYY-MM-DD_HHMM.pdf` — das Original bleibt.

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

Vercel-Projekt: Root Directory `tools/rezept-stempel/web`, Framework Vite, Output `dist`. Keine Env-Vars, keine Serverless Functions.
