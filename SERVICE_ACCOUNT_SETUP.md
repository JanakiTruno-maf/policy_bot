# Service Account Setup

Your service account needs these IAM roles:

```bash
# Add required roles to service account
gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Enable required APIs
gcloud services enable run.googleapis.com --project=bat-bigquery
gcloud services enable artifactregistry.googleapis.com --project=bat-bigquery
gcloud services enable cloudbuild.googleapis.com --project=bat-bigquery
```