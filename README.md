
# Vertex AI RAG Chatbot — Simple Web UI (Cloud Run)

This package adds a **minimal web UI** on `/` so you can ask questions and see answers with **inline citations** and a **Sources** list.

## Deploy
```bash
gcloud run deploy chatbot --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars RAG_CORPUS_RESOURCE="projects/123/locations/us-central1/ragCorpora/abc"
```

## Use
Open the service URL in your browser. Type your question and press **Ask**.
- The **Answer** area shows the model text with inline markers like `[1]`.
- **Sources** lists clickable links (and retrieval scores).

## API
`POST /chat` → `{ response, annotated_text, response_markdown, sources, grounding_metadata, grounding_sources }`
