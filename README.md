# Arkiv — Production Deployment

This branch is the deployment log. Today I moved the entire Arkiv app from local dev into a proper cloud production setup on Google Cloud Platform — frontend, backend, database, auth, secrets, the whole thing.

The `main` branch has the app itself. This README documents how it got from "runs on my laptop" to "running in production end-to-end."

---

## What I Did

- **Frontend** (React/Vite) → deployed to **Firebase Hosting**
- **Backend** (FastAPI) → containerized with Docker, deployed to **Cloud Run**
- **Database** (MySQL) → migrated from local MySQL to **Cloud SQL**
- **Docker + Artifact Registry** deployment pipeline set up
- **Secret Manager + IAM service accounts** configured for secure env injection
- **Google OAuth** auth flow integrated end-to-end

By the end of it the full production stack was live with Google sign-in working.

---

## Final Architecture

```
Users
  ↓
Firebase Hosting   →  React/Vite frontend
  ↓
Cloud Run          →  FastAPI backend
  ↓
Cloud SQL          →  MySQL database

Secret Manager     →  env secrets injected into Cloud Run
Artifact Registry  →  Docker images
IAM / Service Acc  →  Cloud Run identity + permissions
```

Frontend lives at `arkiv-app.web.app`. Backend runs on Cloud Run in `asia-south1`. The two are wired via `VITE_API_URL` at build time and CORS allowlisting on the API side.

---

## The Big Lesson

The single biggest thing I took away from this is **how cloud services actually connect together in production**. Cloud Run doesn't just "talk" to the database the way `localhost:3306` does. You have to:

- enable the right APIs
- create a service account
- give that service account the right IAM roles (Secret Manager accessor, Cloud SQL client)
- attach the Cloud SQL instance to the Cloud Run service so it connects through a socket, not over the public internet
- inject secrets from Secret Manager as env vars at runtime, not bake them into the image

None of that is one command. It's a chain of permissions and bindings, and any missing link silently breaks the service.

---

## Problems I Hit (and Fixed)

### 1. Cloud Run container failing to start

Deployment would say "deployed successfully" but the container crashed during startup. The Cloud Run UI just shows generic errors.

Fix: read the actual logs.

```bash
gcloud run services logs read arkiv-api --region=asia-south1 --limit=50
```

Lesson: Cloud Run logs are mandatory. The dashboard hides the real traceback.

### 2. Malformed env JSON for CORS origins

I was originally loading CORS origins from an env var as JSON:

```python
_origins = json.loads(_raw_origins)
```

PowerShell's escaping mangled the value on the way in and I got `JSONDecodeError` on startup. I dropped the JSON-env approach entirely and hardcoded the allowlist:

```python
_origins = [
    "http://localhost:5173",
    "https://arkiv-app.web.app",
    "https://arkiv-app.firebaseapp.com",
]
```

Lesson: simpler configs deploy more reliably. Don't push JSON through env vars if you don't have to.

### 3. Docker build context blowing up to 266 MB

First `docker build` was copying `.venv`, `frontend/node_modules`, `.git`, and other local junk into the build context. Took forever and the resulting image was huge.

Fix: a real `.dockerignore`.

```
.venv
.git
__pycache__
.vscode
frontend/node_modules
frontend/dist
*.pyc
.env
.env.*
```

Build context dropped from **266 MB → 4 KB**.

Lesson: `.dockerignore` is not optional. Docker copies the entire current folder into the build context unless you tell it not to.

### 4. Firebase wouldn't recognize the project

I created the GCP project first, then tried `firebase init` — got "No Firebase projects associated."

Fix: open the Firebase Console and manually attach Firebase to the existing GCP project. Firebase is a layer on top of GCP, not the same thing.

Lesson: Firebase and GCP are linked but separately initialized. You can't assume `gcloud projects create` also creates a Firebase project.

### 5. OAuth audience mismatch (the worst one)

This one took the longest. The Google sign-in popup worked fine on the frontend, but the backend kept rejecting every token with:

```
Invalid Google token: Token has wrong audience
```

The expected and actual values *looked* identical when printed. After a lot of staring, I diff'd them as bytes and found the expected audience had a trailing `\r\n` — a hidden CRLF that PowerShell had injected when I pushed the value into Secret Manager.

Fix in `api.py`:

```python
# Before
_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# After
_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
```

Lesson: invisible whitespace in secrets is a real thing, especially on Windows. `.strip()` your auth-critical env vars on the way in.

---

## Deployment Walkthrough

The rough order I went through, with the gotchas.

### 1. GCP project

Created project `arkiv-app`. Project IDs are permanent. Billing attaches to the project. Cloud Run, Cloud SQL, Firebase, Secret Manager all live under it.

### 2. Tooling

```bash
gcloud version
firebase --version
docker --version
```

### 3. Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  firebase.googleapis.com \
  iam.googleapis.com
```

Every service is a separate API that has to be turned on.

### 4. Cloud SQL

First attempt failed because I asked for `--storage-size=1GB`. Minimum is 10 GB.

```bash
gcloud sql instances create arkiv-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00

gcloud sql databases create arkiv --instance=arkiv-db
gcloud sql users create arkiv --instance=arkiv-db --password=YOUR_PASSWORD
```

Then loaded `store/schema.sql` and the migration data through the Cloud SQL proxy.

### 5. Secret Manager

Created three secrets:
- `arkiv-mysql-url` — the SQLAlchemy connection string (using the Cloud SQL socket path)
- `arkiv-jwt-secret` — JWT signing secret
- `arkiv-google-client-id` — OAuth client ID for token verification

Secrets get injected into Cloud Run at runtime. Never committed, never in the image.

### 6. Docker

```bash
docker build -t asia-south1-docker.pkg.dev/arkiv-app/arkiv/api:latest .
docker push asia-south1-docker.pkg.dev/arkiv-app/arkiv/api:latest
```

Artifact Registry is just the image host. Cloud Run pulls from it.

### 7. Service account

```bash
gcloud iam service-accounts create arkiv-api-sa \
  --display-name="Arkiv API Service Account"
```

Granted it: Secret Manager accessor, Cloud SQL client. Cloud Run runs *as* this account, so anything the backend needs to reach has to be granted to it explicitly.

### 8. Cloud Run

```bash
gcloud run deploy arkiv-api \
  --image=asia-south1-docker.pkg.dev/arkiv-app/arkiv/api:latest \
  --region=asia-south1 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=arkiv-api-sa@arkiv-app.iam.gserviceaccount.com \
  --add-cloudsql-instances=arkiv-app:asia-south1:arkiv-db \
  --set-secrets="MYSQL_URL=arkiv-mysql-url:latest,JWT_SECRET=arkiv-jwt-secret:latest,GOOGLE_CLIENT_ID=arkiv-google-client-id:latest" \
  --port=8080 \
  --min-instances=0 \
  --max-instances=2
```

First successful hit returned `{"detail":"Not authenticated"}` — which is exactly right. The backend was up, auth middleware was guarding routes, the DB was connected. A 401 here meant everything worked.

### 9. Firebase Hosting

```bash
firebase init hosting
# existing project: arkiv-app
# public dir: frontend/dist
# SPA rewrite: yes
```

Production env in `frontend/.env.production`:

```
VITE_API_URL=https://arkiv-api-<region-host>.run.app
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
```

```bash
cd frontend
npm run build
cd ..
firebase deploy --only hosting
```

I also separated `.env.local` and `.env.production` so dev hits localhost and prod hits Cloud Run automatically based on which build is running.

### 10. Google OAuth

Created an OAuth client (Web application) with three authorized origins:

```
http://localhost:5173
https://arkiv-app.web.app
https://arkiv-app.firebaseapp.com
```

OAuth origins are strict. No trailing slashes. Any missing origin → silent auth failure in the browser console.

---

## Final State

```
Firebase Hosting   →  React frontend
Cloud Run          →  FastAPI backend
Cloud SQL          →  MySQL database
Secret Manager     →  env secrets
Artifact Registry  →  Docker images
IAM Service Acc.   →  Cloud Run identity
Google OAuth       →  Auth flow
```

The full app, including Google sign-in, is running in production end-to-end. From "works on my machine" → "works on the internet" in one (long) day.
