# Arkiv

A personal book collection manager — track what you own, what you're reading, what you've lent, what you want next.

REST API + React SPA: FastAPI backed by MySQL, consumed by a Vite + React frontend.

## Architecture

![Architecture — React + FastAPI + MySQL](docs/diagrams/architecture.png)

Browser loads the React SPA from Vite on `:5173`. The SPA calls the FastAPI server on `:5000`, which talks to MySQL through SQLAlchemy Core in `store/mysql.py`. No ORM models — plain pure functions returning dicts.

## Running it

```bash
# API
uvicorn api:app --reload --port 5000
# Frontend
cd frontend && npm install && npm run dev
```

MySQL schema lives at [`store/schema.sql`](store/schema.sql). Apply with:

```bash
mysql -u arkiv -p arkiv < store/schema.sql
```

Connection via `MYSQL_URL` env var, e.g. `mysql+pymysql://arkiv:<pwd>@localhost:3306/arkiv`.

## Data model

![ER diagram — authors, books, wishlist, activity, profile](docs/diagrams/er.png)

Five tables: `authors`, `books` (aggregate root), `wishlist`, `activity`, `profile`. Books are keyed by ISBN-13 and hold lending info inline (`borrower`, `due_date`). Authors have an 8-char UUID ID (`author_<uuid8>`) and are referenced by `books.author_id` as a foreign key.

## API request flow

![Sequence diagram — GET /books request flow](docs/diagrams/api-flow.png)

Walks through `GET /books?sort=title` end-to-end — click in the browser, `fetch()` from React, route handler in FastAPI, SQLAlchemy call, MySQL query, JSON back to the SPA.

## Evolution

![Timeline — four stages from CLI to MySQL](docs/diagrams/evolution.png)

Arkiv grew through four stages, each on its own branch:

| Stage | Branch | Stack |
| --- | --- | --- |
| 01 · CLI | [`cli`](../../tree/cli) | argparse + `data.json` |
| 02 · Frontend | [`frontend`](../../tree/frontend) | React + Vite, no backend |
| 03 · Salesforce | [`saleforce`](../../tree/saleforce) | FastAPI + Salesforce (SOQL) |
| 04 · MySQL | `main` | FastAPI + SQLAlchemy + MySQL |

Each branch carries its own architecture diagram under `docs/diagrams/` showing what the stack looked like at that point.

## Frontend routes

![Route tree — /, /discover, /book/:id, /author/:id, /profile](docs/diagrams/routes.png)

Five pages behind `BrowserRouter`: `/` (Home), `/discover`, `/book/:id`, `/author/:id`, `/profile`. UI components in `frontend/src/components/ui/` built on Base UI + Tailwind v4, design system is "Quiet Library" — warm linen light, deep walnut dark.
