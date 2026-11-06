# Todo App (FastAPI + JavaScript)

Applicazione full-stack di gestione task con registrazione, login e dati separati per utente.
Progetto di apprendimento: backend REST in Python, frontend in JavaScript vanilla.

**Demo online**
- Applicazione: https://my-first-api-frontend.onrender.com/
- Documentazione API (Swagger): https://my-first-api-vtlr.onrender.com

> Il server è sul piano gratuito di Render: il primo caricamento può richiedere circa un minuto.

## Funzionalità
- Registrazione e login con token JWT (scadenza 30 minuti), password salvate con bcrypt
- CRUD dei task: ogni utente vede e modifica solo i propri (verificato nei test)
- Validazione dei dati con Pydantic, rate limiting su login e registrazione
- Frontend senza framework; i dati utente vengono mostrati con `textContent` (nessun `innerHTML`)

## Stack
Python 3.12 · FastAPI · SQLAlchemy 2 · PostgreSQL (SQLite in locale) · bcrypt · python-jose · pytest · Docker

## Avvio con Docker
```bash
cp .env.example .env        # poi imposta SECRET_KEY (vedi sotto)
docker compose up --build
```
Frontend: http://localhost:3000 · API e documentazione: http://localhost:8000/docs

## Avvio senza Docker
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # imposta SECRET_KEY
python run.py                                      # API su http://localhost:8000
cd frontend && python -m http.server 3000          # frontend su http://localhost:3000
```
Genera una chiave: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## Variabili d'ambiente
| Nome | Obbligatoria | Descrizione |
|---|---|---|
| `SECRET_KEY` | sì | chiave per firmare i JWT; senza, l'app non parte |
| `DATABASE_URL` | no | default SQLite locale; in produzione usa PostgreSQL |
| `ALLOWED_ORIGINS` | no | origini CORS consentite, separate da virgola |

## Test
```bash
pytest -q
```
I test girano anche su GitHub Actions a ogni push.

## Limiti noti
- Il token è in `localStorage`: accettabile per un progetto didattico, ma esposto a XSS in caso di bug
- Nessuna migrazione del database (Alembic) né refresh token
- Sul piano gratuito di Render il server si addormenta dopo un periodo di inattività
