# 🗂️ Arkiv — Production Deployment Journey

> Production deployment + infra setup walkthrough for the Arkiv app.
> This repo/branch documents the entire deployment process, debugging journey, architecture decisions, mistakes, fixes, and final production setup.

---

## Overview

Arkiv is now fully production deployed on **Google Cloud Platform**.

### Current Stack

```
Users
   ↓
Firebase Hosting  (React/Vite frontend)
   ↓
Cloud Run         (FastAPI backend)
   ↓
Cloud SQL         (MySQL)
```

### Additional Infrastructure & Services

| Service | Role |
|---|---|
| Docker | Containerization |
| Artifact Registry | Image storage |
| Secret Manager | Secure env injection |
| IAM Service Accounts | Permission management |
| Google OAuth | Authentication |
| Firebase Hosting | Frontend delivery |

---

## 🌐 Final Production URLs

| Layer | URL |
|---|---|
| **Frontend** | https://arkiv-app.web.app |
| **Backend** | https://arkiv-api-422579343870.asia-south1.run.app |

---

## ✅ What This Deployment Achieved

### Frontend
- React/Vite frontend deployed to Firebase Hosting
- Production environment configuration added
- SPA routing configured properly
- Connected frontend to production backend

### Backend
- FastAPI backend containerized using Docker
- Backend deployed to Cloud Run
- Production secrets injected securely
- Connected to Cloud SQL using secure sockets

### Database
- MySQL migrated to Cloud SQL
- Dedicated DB + DB user created
- Cloud SQL secure connection configured

### Infrastructure
- Docker deployment pipeline setup
- Artifact Registry setup
- Secret Manager integration
- IAM service account permissions configured
- Google OAuth production flow configured

---

## 💀 Biggest Problems Faced

### 1. Cloud Run Container Startup Failures

**Problem:**
```
container failed to start
```

**What happened:**
- Deployment itself succeeded
- But the container crashed during startup
- Cloud Run UI only showed generic errors

**Fix:** Used Cloud Run logs to inspect the actual traceback

```bash
gcloud run services logs read arkiv-api --region=asia-south1 --limit=50
```

> 💡 **What I learned:** Cloud Run logs are mandatory for debugging. Generic deployment errors usually hide the real issue.

---

### 2. ALLOWED_ORIGINS JSON Formatting Issue

**Problem:**
```
JSONDecodeError
```

**Cause:** Environment variable JSON formatting broke. PowerShell escaping corrupted the value.

**Original code:**
```python
_origins = json.loads(_raw_origins)
```

**Temporary fix:**
```python
_origins = ["http://localhost:5173"]
```

**Final production version:**
```python
_origins = [
    "http://localhost:5173",
    "https://arkiv-app.web.app",
    "https://arkiv-app.firebaseapp.com",
]
```

> 💡 **What I learned:** Infra bugs are often config formatting issues. PowerShell escaping can silently break configs. Simpler configs reduce deployment friction.

---

### 3. Docker Build Context Issue

**Problem:**
```
266MB build context
```

**Cause:** These were getting copied into Docker build context:
- `.venv`
- `frontend/node_modules`
- unnecessary local files

**Fix:** Created `.dockerignore`

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

**Result:** `266MB → 4KB` build context

> 💡 **What I learned:** Docker copies the current folder into build context. `.dockerignore` is extremely important. Local environments should never be copied into containers.

---

### 4. Firebase Project Linking Issue

**Problem:**
```
No Firebase projects associated
```

**Cause:** GCP project was created outside Firebase.

**Fix:** Linked Firebase manually through Firebase Console.

> 💡 **What I learned:** Firebase can attach onto existing GCP projects. The Firebase layer is separate from base GCP project creation.

---

### 5. OAuth Audience Mismatch Issue

> ⚠️ This was the most annoying bug during deployment.

**Problem:**
```
Invalid Google token
```

**Backend logs showed:**
```
Token has wrong audience
```

**After debugging:**

| | Value |
|---|---|
| Expected | `clientid.apps.googleusercontent.com\r\n` |
| Actual | `clientid.apps.googleusercontent.com` |

**Cause:** Hidden newline characters inside Secret Manager value. PowerShell injected hidden CRLF characters.

**Final fix:**

```python
# Before
_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# After
_GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "").strip()
```

> 💡 **What I learned:** Hidden whitespace can completely break auth. `.strip()` hardens env variable handling. Infra debugging sometimes involves invisible characters.

---

## 🚀 Full Deployment Walkthrough

### 1. GCP Project Setup

Created project: `arkiv-app`

> **Learned:**
> - Project IDs are permanent
> - Billing is attached to project
> - Firebase, Cloud Run, Cloud SQL all operate under the same project

---

### 2. Installed Required Tooling

Installed:
- `gcloud`
- `firebase-tools`
- `docker desktop`

Verification:
```bash
gcloud version
firebase --version
docker --version
```

---

### 3. Enabled Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  firebase.googleapis.com \
  iam.googleapis.com
```

> **Learned:** GCP services are modular APIs. Services must be enabled before usage.

---

### 4. Cloud SQL Setup

**Initial mistake:**
```bash
--storage-size=1GB
# Error: minimum is 10GB
```

**Created instance:**
```bash
gcloud sql instances create arkiv-db \
  --database-version=MYSQL_8_0 \
  --tier=db-f1-micro \
  --region=asia-south1 \
  --storage-type=SSD \
  --storage-size=10GB \
  --backup-start-time=03:00
```

**Created DB:**
```bash
gcloud sql databases create arkiv --instance=arkiv-db
```

**Created DB user:**
```bash
gcloud sql users create arkiv --instance=arkiv-db --password=YOUR_PASSWORD
```

---

### 5. Secret Manager Setup

Created secrets for:
- JWT secret
- MySQL URL
- Google Client ID

> **Learned:** Never hardcode secrets into code. Cloud Run can inject secrets directly as env vars.

---

### 6. Docker Setup

**Build image:**
```bash
docker build -t asia-south1-docker.pkg.dev/arkiv-app/arkiv/api:latest .
```

**Push image:**
```bash
docker push asia-south1-docker.pkg.dev/arkiv-app/arkiv/api:latest
```

> **Learned:** Docker image = packaged runtime environment. Artifact Registry stores deployable containers.

---

### 7. IAM Service Account Setup

**Created service account:**
```bash
gcloud iam service-accounts create arkiv-api-sa \
  --display-name="Arkiv API Service Account"
```

Added permissions:
- Secret Manager access
- Cloud SQL client access

> **Learned:** Cloud Run executes as a service account. Backend needs explicit permissions to access infra.

---

### 8. Cloud Run Deployment

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

**Verified successful deployment using:**
```json
{"detail":"Not authenticated"}
```

> **Learned:** `401` can mean a healthy protected backend. Backend + auth middleware + DB connection were all working.

---

### 9. Firebase Hosting Setup

**Initialized Firebase Hosting:**
```bash
firebase init hosting
```

Selected:
- existing project
- `arkiv-app`
- `frontend/dist`
- SPA rewrite enabled

**Production env:**
```env
VITE_API_URL=https://arkiv-api-422579343870.asia-south1.run.app
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
```

**Deploy:**
```bash
cd frontend
npm run build

cd ..
firebase deploy --only hosting
```

---

### 10. OAuth Setup

Created OAuth client as: **Web application**

**Authorized origins:**
```
http://localhost:5173
https://arkiv-app.web.app
https://arkiv-app.firebaseapp.com
```

> **Learned:** Google OAuth origins are extremely strict. Missing origins silently break authentication. No trailing slash allowed.

---

## 🧠 Final Infra Concepts Learned

### Cloud Run
- Runs containers, not raw Python code
- Pulls Docker images from Artifact Registry
- Uses service accounts for permissions

### Docker
- Packages application runtime
- Build context size matters heavily
- `.dockerignore` is critical

### Cloud SQL
- Secure managed MySQL
- Uses proxy/socket connection
- Separate instance, database, and user concepts

### Secret Manager
- Secure env variable injection
- Better than storing secrets in code or `.env`

### Firebase Hosting
- Serves frontend static files
- Handles SPA routing
- Can connect to existing GCP projects

---

## 🏁 Final State

Fully working production stack:

- ✅ Cloud Run backend
- ✅ Firebase Hosting frontend
- ✅ Cloud SQL database
- ✅ Google OAuth
- ✅ JWT auth
- ✅ Secret Manager
- ✅ Docker deployment pipeline
- ✅ Artifact Registry
- ✅ IAM service accounts

**Everything deployed and working end-to-end.**