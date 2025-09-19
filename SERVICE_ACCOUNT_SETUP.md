# Service Account Setup

Your service account needs these IAM roles:

```bash
# Minimal permissions needed (ask project admin to run these):

# Enable required APIs
gcloud services enable run.googleapis.com --project=bat-bigquery
gcloud services enable cloudbuild.googleapis.com --project=bat-bigquery
gcloud services enable containerregistry.googleapis.com --project=bat-bigquery

# Add minimal roles to service account
gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding bat-bigquery \
  --member="serviceAccount:gemini-chat-bq@bat-bigquery.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```