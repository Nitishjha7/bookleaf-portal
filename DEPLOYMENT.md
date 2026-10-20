# Deploying to GCP (Cloud Run)

Two Cloud Run services (`bookleaf-api` and `bookleaf-web`) and a Cloud SQL Postgres database.
Secrets live in Secret Manager. GitHub Actions builds the images and deploys on every push to `main`.

If you don't want to pay for Cloud SQL for a demo, you can leave out the `DATABASE_URL` secret (and
the `--add-cloudsql-instances` flag in `deploy.yml`). The API then uses SQLite inside the container,
which works but resets whenever Cloud Run starts a new instance.

Replace the values at the top with your own.

## 1. One-time setup

```bash
export PROJECT_ID=your-project-id
export REGION=asia-south1
export GH_REPO=your-github-user/bookleaf-portal

gcloud config set project $PROJECT_ID

gcloud services enable run.googleapis.com artifactregistry.googleapis.com \
  sqladmin.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com

gcloud artifacts repositories create bookleaf --repository-format=docker --location=$REGION
```

### Database

```bash
gcloud sql instances create bookleaf-db --database-version=POSTGRES_16 \
  --tier=db-f1-micro --region=$REGION
gcloud sql databases create bookleaf --instance=bookleaf-db
gcloud sql users create bookleaf --instance=bookleaf-db --password=CHOOSE_A_PASSWORD
```

The connection name is `PROJECT_ID:REGION:bookleaf-db`.

### Secrets

```bash
python -c "import secrets; print(secrets.token_hex(32))" | gcloud secrets create bookleaf-secret-key --data-file=-
printf '%s' "YOUR_GEMINI_KEY" | gcloud secrets create bookleaf-gemini-key --data-file=-
printf '%s' "postgresql://bookleaf:CHOOSE_A_PASSWORD@/bookleaf?host=/cloudsql/$PROJECT_ID:$REGION:bookleaf-db" \
  | gcloud secrets create bookleaf-database-url --data-file=-
```

Get a Gemini key at https://aistudio.google.com/apikey.

### Service accounts

```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# used by GitHub Actions to deploy
gcloud iam service-accounts create gh-deployer
DEPLOYER=gh-deployer@$PROJECT_ID.iam.gserviceaccount.com
for role in run.admin artifactregistry.writer iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$DEPLOYER --role=roles/$role
done

# the account Cloud Run runs as needs the secrets and the database
RUNTIME=$PROJECT_NUMBER-compute@developer.gserviceaccount.com
for role in secretmanager.secretAccessor cloudsql.client; do
  gcloud projects add-iam-policy-binding $PROJECT_ID --member=serviceAccount:$RUNTIME --role=roles/$role
done
```

### Letting GitHub deploy without a key file (Workload Identity Federation)

```bash
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global --workload-identity-pool=github \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository \
  --attribute-condition="assertion.repository=='$GH_REPO'"

gcloud iam service-accounts add-iam-policy-binding $DEPLOYER \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$GH_REPO"
```

### GitHub settings

Repo, Settings, Secrets and variables, Actions.

Secrets:

| Name | Value |
|------|-------|
| `GCP_WIF_PROVIDER` | `projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/github-provider` |
| `GCP_DEPLOY_SA` | `gh-deployer@PROJECT_ID.iam.gserviceaccount.com` |

Variables:

| Name | Value |
|------|-------|
| `GCP_PROJECT_ID` | your project id |
| `GCP_REGION` | for example `asia-south1` |
| `CLOUDSQL_CONNECTION` | `PROJECT_ID:REGION:bookleaf-db` |
| `WEB_URL` | the frontend URL, see below |

## 2. First deploy

The API needs the frontend URL for CORS and the frontend needs the API URL, so the first deploy
takes two runs.

1. Push to `main` (or start the Deploy workflow by hand) with `WEB_URL` set to any placeholder.
   Both services get deployed.
2. Get the real frontend URL, put it in the `WEB_URL` variable and run the workflow again:

   ```bash
   gcloud run services describe bookleaf-web --region $REGION --format='value(status.url)'
   ```

The URLs don't change after that, so later pushes to `main` just redeploy.

## 3. Check it

```bash
curl https://YOUR-API-URL/api/health
```

It should return `"status":"ok"` and `"ai_active":true`. Then open the frontend URL and log in with the
accounts from the README. The database is seeded the first time the API container starts.

## Notes

- Cloud SQL `db-f1-micro` costs a few dollars a month. When you're done with the demo, delete it:
  `gcloud sql instances delete bookleaf-db`.
- Cloud Run scales to zero, so the first request after a quiet period takes a few seconds.
- The frontend needs the API URL at build time (`VITE_API_BASE`), which is why the workflow does
  `docker build --build-arg` instead of `gcloud run deploy --source`.
