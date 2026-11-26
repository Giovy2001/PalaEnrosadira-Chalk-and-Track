# 🧗 Chalk & Track

Web app semi-ufficiale di **PalaEnrosadira** per tracciare, esplorare e condividere blocchi di boulder in palestra.

---

## Funzionalità

### 👤 Utenti
- Creazione profilo e accesso mediante token firmato, con sessione lato server.
- Profilo con punti, tag in base al punteggio, grado più elevato e blocchi creati/completati.
- Cambio colore del profilo (8 colori) sincronizzato con il database.

### 🧩 Blocchi di Boulder
- Creazione in tre passaggi: foto → prese → nome/grado/descrizione.
- Selezione e drag delle prese con tipologia (start, middle, zone, top) e vincoli (piede, solo mani, ecc.).
- Grado opzionale, modificabile in seguito.
- Visualizzazione dettagli con legenda e beta.
- Modifica ed eliminazione riservate all'autore (verifica lato server).

### 🔍 Esplora e Archivio
- Feed dei blocchi recenti, con esclusione di quelli già completati.
- Archivio con filtri per nome, autore e difficoltà.
- Punti e storico dei completamenti aggiornati automaticamente.

---

## Tech Stack

**Backend**: Python 3.12, Flask (application factory), libsql (SQLite locale / Turso), Vercel Blob, Pillow.

**Frontend**: HTML + Jinja2 (template base condiviso), CSS statici, JavaScript vanilla.

**Deploy**: Vercel serverless (`@vercel/python`), cron settimanale di pulizia.

---

## Sviluppo locale

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
pip install -r requirements-dev.txt
cp .env.example .env            # compilare SECRET_KEY (obbligatoria anche in locale)
python main.py                  # http://127.0.0.1:8080
```

La modalità locale viene rilevata da `APP_ENV=local` (predefinito fuori da Vercel).
Il database locale si trova in `static/local_database/sql_database.db`.
Per azzerarlo: `python static/local_database/wipe_database.py`.
Le icone PWA e quelle dei 8 colori profilo si rigenerano con `python scripts/generate_icons.py`.

### Test

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

I test usano un database temporaneo e non toccano mai i dati locali.

---

## Deploy su Vercel

Configurare le variabili d'ambiente nel progetto Vercel:

| Variabile | Descrizione |
|---|---|
| `SECRET_KEY` | Segreto per sessioni e token (obbligatorio) |
| `TURSO_DATABASE_URL` | URL del database Turso |
| `TURSO_AUTH_TOKEN` | Token di autenticazione Turso |
| `BLOB_READ_WRITE_TOKEN` | Token di Vercel Blob |
| `CRON_SECRET` | Segreto per il cron di pulizia (se vuoto, cron disabilitato) |
| `ALLOW_LEGACY_CLAIM` | `1` solo per la migrazione una tantum dei profili senza token |

Il deploy avviene dal branch configurato su Vercel. `main` e `develop` sono entrambi
coperti dalla CI; verificare quale dei due è collegato alla produzione.

Le migrazioni dello schema vengono applicate automaticamente all'avvio
(`scripts/database_sql/migrations.py`): non è più necessario droppare le tabelle a mano.

Endpoint di controllo: `GET /health`.

---

## Sicurezza

- L'identità non si basa più su `localStorage`: le scritture richiedono una sessione
  Flask o un token firmato (`itsdangerous`) associato all'utente nel database.
- `localStorage` conserva solo una preferenza di interfaccia e il token per
  ripristinare la sessione dopo un cold start.
- Modifica/eliminazione delle route sono protette da `require_author()` lato server.
- Cron di pulizia protetto da `CRON_SECRET` (header `Authorization: Bearer ...`).
- Nessun segreto è versionato: vedere `.env.example` e `.gitignore`.
