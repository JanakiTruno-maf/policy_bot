# Missing Configuration Setup

Your app is deployed but needs these configurations:

## 1. RAG Corpus Resource
Replace `YOUR_RAG_CORPUS_ID` in cloudbuild.yaml with your actual RAG corpus ID:
```
RAG_CORPUS_RESOURCE=projects/bat-bigquery/locations/us-central1/ragCorpora/YOUR_ACTUAL_CORPUS_ID
```

## 2. OAuth Configuration (Optional)
If you want Google OAuth login, add these environment variables:
```bash
gcloud run services update maf-policy-bot-7d1bbb0e \
  --region=us-central1 \
  --set-env-vars="GOOGLE_CLIENT_ID=your-client-id,GOOGLE_CLIENT_SECRET=your-client-secret"
```

## 3. Current Issues:
- **OAuth not configured**: App will show "OAuth not configured" error
- **RAG corpus missing**: Chat functionality won't work without valid corpus ID
- **Templates missing**: Login/index templates may not render properly

## 4. Quick Fix - Deploy with correct RAG corpus:
1. Update `cloudbuild.yaml` with your RAG corpus ID
2. Run: `gcloud builds submit --config cloudbuild.yaml --project=bat-bigquery`

## 5. Check logs:
```bash
gcloud logs read --project=bat-bigquery --filter="resource.type=cloud_run_revision"
```