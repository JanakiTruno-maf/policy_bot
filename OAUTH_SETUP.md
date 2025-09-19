# OAuth Setup Guide

## 1. Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project or create a new one
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth 2.0 Client IDs**
5. Choose **Web application**
6. Add authorized redirect URIs:
   - For local development: `http://localhost:8080/login/callback`
   - For Cloud Run: `https://YOUR-SERVICE-URL/login/callback`

## 2. Set Environment Variables

Copy your `.env.example` to `.env` and update:

```bash
# Your existing variables
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_LOCATION=us-central1
VERTEX_MODEL_NAME=gemini-2.0-flash-001
RAG_CORPUS_RESOURCE=projects/123/locations/us-central1/ragCorpora/abc

# OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-random-secret-key-for-sessions
```

## 3. Deploy to Cloud Run

Update your deploy command to include OAuth environment variables:

```bash
gcloud run deploy chatbot --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars RAG_CORPUS_RESOURCE="projects/123/locations/us-central1/ragCorpora/abc" \
  --set-env-vars GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com" \
  --set-env-vars GOOGLE_CLIENT_SECRET="your-client-secret" \
  --set-env-vars SECRET_KEY="your-random-secret-key"
```

## 4. Update OAuth Redirect URI

After deployment, update your Google OAuth credentials with the actual Cloud Run URL:
- `https://your-actual-service-url/login/callback`

## Features Added

- ✅ Google OAuth authentication
- ✅ User session management
- ✅ Protected chat endpoints
- ✅ User info display in header
- ✅ Logout functionality
- ✅ Responsive login page

## Security Notes

- Sessions are secured with SECRET_KEY
- All chat endpoints require authentication
- User info is stored in secure sessions
- OAuth tokens are handled securely