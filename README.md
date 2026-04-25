# Arkiv

A personal book collection manager — track what you own, what you're reading, what you've lent, and what you want next.

A REST API + React SPA: **FastAPI** backed by **MySQL**, consumed by a **Vite + React** frontend. Designed around a quiet, library-inspired UI — warm linen by day, deep walnut by night.

## Architecture

![Architecture — React + FastAPI + MySQL](docs/diagrams/architecture.png)

The browser loads the React SPA from Vite on `:5173`. The SPA calls the FastAPI server on `:5000`, which talks to MySQL through SQLAlchemy Core in `store/mysql.py`. No ORM models — just pure functions returning plain dicts.

## Getting started

### Prerequisites

- **Python** 3.11+
- **Node** 20+ (for Vite 5 / React 19)
- **MySQL** 8.0+ running locally (or reachable over the network)
- **Git**

### 1. Clone

```bash
git clone <your-fork-url> arkiv
cd arkiv
```

### 2. Set up MySQL

Connect as a user with `CREATE` privileges (often `root`) and create the database + an app user:

```sql
CREATE DATABASE arkiv CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'arkiv'@'localhost' IDENTIFIED BY 'your-password-here';
GRANT ALL PRIVILEGES ON arkiv.* TO 'arkiv'@'localhost';
FLUSH PRIVILEGES;
```

Apply the schema (five tables — `authors`, `books`, `wishlist`, `activity`, `profile`):

```bash
mysql -u arkiv -p arkiv < store/schema.sql
```

**(Optional) seed with the migration data.** `migration/load.sql` bulk-loads CSVs from `migration/mysql_ready/` via `LOAD DATA LOCAL INFILE`. Two gotchas:

- The paths inside `load.sql` are **absolute and hardcoded to the original author's machine** — open it and replace each `C:/Users/PC/dev/projs/arkiv/...` with your own absolute path before running.
- `LOCAL INFILE` is disabled by default in MySQL 8. Enable it on both ends:
  ```sql
  SET GLOBAL local_infile = 1;
  ```
  ```bash
  mysql --local-infile=1 -u arkiv -p arkiv < migration/load.sql
  ```

If you skip seeding, the app starts empty and you add books through the UI.

### 3. Configure the backend

Create a `.env` file in the repo root (it's git-ignored):

```dotenv
MYSQL_URL=mysql+pymysql://arkiv:your-password-here@localhost:3306/arkiv
```

`store/mysql.py` calls `load_dotenv()` at import time, so you don't need to export anything manually.

### 4. Run the API

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload --port 5000
```

Sanity checks:

- http://localhost:5000/docs — Swagger UI, every route listed
- http://localhost:5000/api/books — should return `[]` (or your seeded rows)
- `python scripts/test_mysql_layer.py` — exercises the store layer end-to-end

If the API logs `db_unavailable`, MySQL isn't reachable or `MYSQL_URL` is wrong.

### 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api/*` to `http://localhost:5000` (configured in `frontend/vite.config.js`), so the frontend has **no env file** — it just works as long as the API is on `:5000`.

### What you shouldn't change

A few things are wired together and will break quietly if you move them:

- **Ports.** The API CORS allowlist in `api.py` hardcodes `http://localhost:5173`, and the Vite proxy hardcodes `http://localhost:5000`. If you change one port, change both.
- **`store/schema.sql`** is the source of truth for the schema. Don't edit tables ad-hoc through a GUI — alter `schema.sql` and re-apply, so the next person cloning gets the same shape.
- **`store/__init__.py`** is intentionally empty — `api.py` imports `store.mysql` directly. Don't add re-exports there.
- **`migration/`** is a one-time artifact from the Salesforce → MySQL move. Safe to ignore or delete once you've seeded; not part of normal runtime.
- **Author IDs** are generated as `author_<8-char-uuid>` by the API. Don't insert authors with arbitrary IDs — the books FK will reject them.

## Project layout

```
api.py            FastAPI app — all /api/* routes
store/
  mysql.py        SQLAlchemy Core data layer (pure functions, dict in/out)
  schema.sql      MySQL schema — source of truth
frontend/         Vite + React 19 + Tailwind v4 SPA
  src/lib/api.js  fetch wrapper for the FastAPI server
docs/diagrams/    architecture, ER, sequence, timeline, route diagrams
migration/        SQL + CSV artifacts from the Salesforce → MySQL migration
scripts/          prep_csvs.py, test_mysql_layer.py
```

## Data model

![ER diagram — authors, books, wishlist, activity, profile](docs/diagrams/er.png)

Five tables: `authors`, `books` (aggregate root), `wishlist`, `activity`, `profile`. Books are keyed by ISBN-13 and hold lending info inline (`borrower`, `due_date`); `status` ∈ `{available, lent, reading, sold}`. Authors get an 8-char UUID ID (`author_<uuid8>`) and are referenced by `books.author_id` as a foreign key.

## API request flow

![Sequence diagram — GET /books request flow](docs/diagrams/api-flow.png)

A walkthrough of `GET /books?sort=title` end-to-end — click in the browser, `fetch()` from React, route handler in FastAPI, SQLAlchemy Core call, MySQL query, JSON back to the SPA.

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

Five pages behind `BrowserRouter`: `/` (Home), `/discover`, `/book/:id`, `/author/:id`, `/profile`. UI components in `frontend/src/components/ui/` are built on Base UI + Tailwind v4. The design system — **Quiet Library** — pairs warm linen light with deep walnut dark, set in Lora (headings) and Nunito Sans (body), with `oklch` colors defined in `src/globals.css`.
