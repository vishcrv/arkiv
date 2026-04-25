# Arkiv — stage 03 · Salesforce

Third stage of Arkiv: the React SPA gets a real backend. FastAPI exposes a REST API, and the data layer lives in Salesforce — custom objects queried via SOQL using `simple_salesforce`.

Stack:

- **React 19** + React Router + Vite (unchanged from the frontend stage)
- **FastAPI** on `:5000` — new
- **`store/sf.py`** — data layer using `simple_salesforce`
- **Salesforce** — custom objects for books, authors, wishlist, activity; SOQL queries with bearer auth

## Architecture

![Salesforce architecture — FastAPI + SOQL](docs/diagrams/architecture.png)

Browser → React SPA → FastAPI → `store/sf.py` → Salesforce. The data layer is swappable — same function names as the legacy JSON store, so `api.py` doesn't know or care what's behind the call.

## Running it

```bash
# Set Salesforce credentials in .env
# SF_USERNAME, SF_PASSWORD, SF_TOKEN, SF_DOMAIN
uvicorn api:app --reload --port 5000
cd frontend && npm install && npm run dev
```

## Next stage

`main` migrates the data layer from Salesforce to MySQL, keeping the API contract identical. The interface held because `store/sf.py` and `store/mysql.py` expose the same pure-function shape.
