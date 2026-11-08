# Todo App (FastAPI + JavaScript)

Applicazione full-stack di gestione task con registrazione, login, recupero password
e dati separati per utente. Progetto di apprendimento: backend REST in Python,
frontend in JavaScript vanilla, deploy su infrastruttura gratuita reale.

**Demo online**
- Applicazione: https://my-first-api-frontend.onrender.com
- Documentazione API (Swagger): https://my-first-api-vtlr.onrender.com/docs

> Il server è sul piano gratuito di Render: il primo caricamento può richiedere circa un minuto.

## Funzionalità

- Registrazione e login con token JWT (scadenza 30 minuti), password salvate con bcrypt
- CRUD dei task: ogni utente vede e modifica solo i propri (verificato nei test)
- Recupero password via email: token ad alta entropia, hash salvato nel database,
  scadenza 30 minuti, uso singolo; invio email tramite Brevo (API gratuita)
- Eliminazione account con riconferma della password
- Validazione dei dati con Pydantic, rate limiting su login, registrazione e reset password
- Frontend senza framework; i dati utente vengono mostrati con `textContent` (nessun `innerHTML`)

## Stack

Python 3.12+ · FastAPI · SQLAlchemy 2 · PostgreSQL (Neon) · bcrypt · python-jose ·
Brevo (email transazionali) · pytest · Docker · GitHub Actions (CI)

## Avvio con Docker

```bash
cp .env.example .env        # poi compila le variabili (vedi sotto)
docker compose up --build
```

Frontend: http://localhost:3000 · API e documentazione: http://localhost:8000/docs

## Avvio senza Docker

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env        # compila le variabili
python run.py                                      # API su http://localhost:8000
cd frontend && python -m http.server 3000           # frontend su http://localhost:3000
```

Genera una chiave: `python -c "import secrets; print(secrets.token_urlsafe(48))"`

## Variabili d'ambiente

| Nome | Obbligatoria | Descrizione |
|---|---|---|
| `SECRET_KEY` | sì | chiave per firmare i JWT; senza, l'app non parte |
| `DATABASE_URL` | no | default SQLite locale; in produzione PostgreSQL (Neon) |
| `ALLOWED_ORIGINS` | no | origini CORS consentite, separate da virgola |
| `BREVO_API_KEY` | per il recupero password | chiave API di Brevo (piano gratuito, 300 email/giorno) |
| `BREVO_SENDER_EMAIL` | per il recupero password | indirizzo mittente verificato su Brevo |
| `FRONTEND_URL` | per il recupero password | URL del frontend, usato per costruire il link nell'email |

## Test

```bash
pytest -q
```

I test girano anche su GitHub Actions a ogni push: autenticazione, isolamento dei dati
tra utenti, eliminazione account, richiesta e conferma del recupero password.

## Database

Il database di produzione è PostgreSQL su Neon (piano gratuito, senza scadenza).
In precedenza il progetto usava il Postgres gratuito di Render, che si cancella
periodicamente e scade dopo 30 giorni: la migrazione a Neon risolve entrambi i problemi
senza richiedere modifiche al codice, perché la connessione è letta da `DATABASE_URL`.

## Recupero password: come funziona

1. L'utente richiede il reset con la propria email (`POST /password-reset/request`).
2. Il server genera un token casuale ad alta entropia, ne salva solo l'hash
   (mai il token in chiaro) con una scadenza di 30 minuti, e lo invia via email.
3. L'endpoint risponde sempre con lo stesso messaggio generico, registrata o meno
   l'email, per non rivelare quali indirizzi sono nel sistema.
4. L'utente clicca il link nell'email, inserisce la nuova password
   (`POST /password-reset/confirm`); il token viene verificato e marcato come usato,
   così non può essere riutilizzato.

Nota: Brevo richiede un mittente verificato ma, a differenza di molti servizi email
gratuiti, non limita l'invio al solo indirizzo del proprietario dell'account: funziona
per qualunque destinatario reale.

## Cosa ho imparato (problemi reali incontrati e risolti)

- **SQLite e PostgreSQL non si comportano allo stesso modo sui vincoli.** In locale
  (SQLite) l'eliminazione di un account con token di reset collegati non dava errore;
  su PostgreSQL (Neon), che applica correttamente i vincoli di integrità referenziale,
  la stessa operazione falliva con un `ForeignKeyViolation`. Corretto aggiungendo
  `cascade="all, delete-orphan"` sulla relazione utente → token di reset.
- **Un errore 500 può mascherarsi da errore CORS.** Quando un endpoint va in crash con
  un'eccezione non gestita, FastAPI/Starlette può restituire la risposta senza gli
  header CORS, e il browser mostra "bloccato da CORS policy" anche se la vera causa è
  un errore nel backend. La diagnosi corretta richiede di controllare i log del server,
  non solo la console del browser.
- **Un valore di default silenzioso può rompere una funzionalità senza errori visibili.**
  `os.getenv('FRONTEND_URL', '')` con stringa vuota come default ha prodotto, in assenza
  della variabile su Render, un link di reset senza dominio (solo `#reset-password?token=...`).
  Aperto dentro Gmail, un link di questo tipo viene interpretato come un'ancora interna
  alla pagina di Gmail stessa, non come un link esterno. Corretto rimuovendo il default
  silenzioso e facendo fallire esplicitamente la richiesta se la variabile manca.
- **SQLite non conserva l'informazione del fuso orario.** Un confronto tra un datetime
  "aware" (`datetime.now(timezone.utc)`) e uno "naive" letto da una colonna
  `DateTime(timezone=True)` su SQLite causa un `TypeError`; non succede su PostgreSQL.
  Corretto normalizzando il fuso orario prima del confronto.

## Prossimi passi possibili

- Migrazioni del database con Alembic, invece di affidarsi a `create_all`
- Refresh token, per evitare login troppo frequenti
- Rimuovere la dipendenza da un browser di terze parti per il tracking dei link email
  (attualmente mitigato inviando il link come testo semplice anziché come `<a href>`)
