# PharmacyExceptions

Lokale Apotheken-Werkzeuge. PEOS bleibt unberührt.

## Rezept-Stempel

Browser-App unter `tools/rezept-stempel/web`.

```bash
cd tools/rezept-stempel/web
npm install
npm run dev
npm run build
```

Production: GitHub → Vercel auto-deploy (`main` = Production, andere Branches = Preview).

- Repo: https://github.com/aboubasem1/rezept-stempel
- Live: https://rezept-stempel.vercel.app
- Vercel Root Directory: `tools/rezept-stempel/web`

Windows: App in Edge/Chrome installieren, dann `.pdf` unter Standard-Apps auf Rezept-Stempel stellen. Details: `tools/rezept-stempel/README.md`.
