import os
import logging
from typing import Any, Dict, List, Tuple
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import requests
from requests_oauthlib import OAuth2Session

load_dotenv()
# Only disable HTTPS requirement for local development
if os.environ.get('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
import vertexai
from vertexai.generative_models import GenerativeModel, Tool
from vertexai import rag

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("PROJECT_ID")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
MODEL_NAME = os.environ.get("VERTEX_MODEL_NAME", "gemini-2.0-flash-001")
RAG_CORPUS = os.environ.get("RAG_CORPUS_RESOURCE")

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid_configuration"
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

if not PROJECT_ID or not RAG_CORPUS:
    logger.warning("Missing GOOGLE_CLOUD_PROJECT/PROJECT_ID or RAG_CORPUS_RESOURCE.")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tobacco-legal-info-system-2024')

# OAuth helper functions
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# System prompt for legal advisory behavior
SYSTEM_PROMPT = """
You are a helpful tobacco legal information assistant that provides factual information from legal documents to help marketing teams understand tobacco regulations. You present facts clearly while being conversational and helpful.

HANDLING DIFFERENT QUERY TYPES:

1. GREETINGS/INTRODUCTIONS:
   - Respond warmly: "Hello! I'm here to help you understand tobacco laws and regulations. I can provide factual information from our legal document database to help with your questions about tobacco legislation, compliance requirements, or market regulations. What would you like to know?"

2. TOBACCO-RELATED QUERIES:
   - Present relevant tobacco laws and regulations from your knowledge base
   - Include country-specific information when available
   - Explain legal requirements and compliance obligations
   - Provide context about regulatory frameworks
   - Present information in a helpful, conversational way

3. MARKETING/BUSINESS QUERIES RELATED TO TOBACCO:
   - Help by explaining relevant legal constraints and requirements
   - Example: "For marketing campaigns, here are the key tobacco advertising regulations you should be aware of..." then provide relevant legal facts
   - Focus on what the law says about marketing, advertising, packaging, etc.

4. OFF-TOPIC QUERIES:
   - Politely redirect: "I focus on tobacco laws and regulations. While I can't help with [topic], I'd be happy to discuss tobacco-related legal matters. Is there anything about tobacco legislation or compliance you'd like to know?"

GUIDELINES:
- Base responses on information from your legal document knowledge base
- Present facts clearly and helpfully
- When information isn't available, say: "I don't have specific information about that in our current legal database. You may want to consult with a legal professional for detailed guidance on this topic."
- Always provide source citations when presenting legal facts
- Be conversational and helpful while staying factual
- Help users understand how tobacco laws might apply to their questions
"""

# -----------------------------
# RAG helpers
# -----------------------------

def build_rag_tool(top_k: int = 5) -> Tool:
    rag_retrieval_config = rag.RagRetrievalConfig(top_k=top_k)
    return Tool.from_retrieval(
        retrieval=rag.Retrieval(
            source=rag.VertexRagStore(
                rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
                rag_retrieval_config=rag_retrieval_config,
            )
        )
    )

def retrieve_contexts(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Return contexts with source_uri, title (source_display_name), text, score."""
    rag_retrieval_config = rag.RagRetrievalConfig(top_k=top_k)
    resp = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
        text=query,
        rag_retrieval_config=rag_retrieval_config,
    )
    contexts: List[Dict[str, Any]] = []
    
    try:
        if hasattr(resp, 'contexts') and resp.contexts is not None:
            for c in resp.contexts.contexts:
                # Extract page information from chunk.page_span
                page_number = None
                page_range = None
                chunk = getattr(c, "chunk", None)
                if chunk and hasattr(chunk, "page_span"):
                    page_span = getattr(chunk, "page_span")
                    if page_span:
                        first_page = getattr(page_span, "first_page", None)
                        last_page = getattr(page_span, "last_page", None)
                        if first_page:
                            page_number = first_page
                            if last_page and last_page != first_page:
                                page_range = f"{first_page}-{last_page}"
                            else:
                                page_range = str(first_page)
                
                contexts.append({
                    "source_uri": convert_gs_to_authenticated_url(getattr(c, "source_uri", None)),
                    "title": getattr(c, "source_display_name", None),
                    "text": getattr(c, "text", None),
                    "score": getattr(c, "score", None),
                    "page_number": page_number,
                    "page_range": page_range,
                })
    except Exception as e:
        logger.warning(f"Could not parse RAG contexts: {e}")
        pass
    
    return contexts

def extract_grounding_from_generation(gen_response) -> Dict[str, Any]:
    """Parse model text + grounding chunks/supports from a GenerationResponse."""
    out: Dict[str, Any] = {"text": getattr(gen_response, "text", None)}
    d = None
    try:
        d = gen_response.to_dict() if hasattr(gen_response, "to_dict") else None
    except Exception:
        d = None
    if d:
        cand0 = (d.get("candidates") or [{}])[0]
        gm = cand0.get("grounding_metadata") or {}
        chunks = []
        for ch in gm.get("grounding_chunks") or []:
            rc = (ch.get("retrieved_context") or {})
            uri = rc.get("uri") or rc.get("source_uri")
            title = rc.get("title") or rc.get("source_display_name")
            text = rc.get("text")
            chunks.append({"uri": uri, "title": title, "text": text})
        out["grounding_chunks"] = chunks
        out["grounding_supports"] = gm.get("grounding_supports") or []
        return out
    # Fallback attribute access
    try:
        c0 = gen_response.candidates[0]
        gm = getattr(c0, "grounding_metadata", None)
        if gm and getattr(gm, "grounding_chunks", None):
            chunks = []
            for ch in gm.grounding_chunks:
                rc = getattr(ch, "retrieved_context", None)
                uri = getattr(rc, "uri", None) if rc else None
                title = getattr(rc, "title", None) if rc else None
                text = getattr(rc, "text", None) if rc else None
                chunks.append({"uri": uri, "title": title, "text": text})
            out["grounding_chunks"] = chunks
            out["grounding_supports"] = getattr(gm, "grounding_supports", [])
    except Exception:
        pass
    return out

# -----------------------------
# Inline citation formatting
# -----------------------------

def _mk_source_key(uri: str, title: str, text: str) -> str:
    if uri: return f"uri::{uri}"
    if title and text: return f"title::{title}::text::{text[:80]}"
    if text: return f"text::{text[:120]}"
    return "unknown"

def build_citation_catalog(
    gen_chunks: List[Dict[str, Any]],
    retrieved: List[Dict[str, Any]]
):
    """Return (index->number map, catalog list)."""
    by_uri = {r.get("source_uri"): r for r in retrieved if r.get("source_uri")}
    by_title = {}
    for r in retrieved:
        t = r.get("title")
        if t and t not in by_title:
            by_title[t] = r

    catalog: List[Dict[str, Any]] = []
    index_to_cite_num: Dict[int, int] = {}

    def ensure_entry(chunk: Dict[str, Any]) -> int:
        uri = chunk.get("uri")
        title = chunk.get("title")
        text = chunk.get("text")
        key = _mk_source_key(uri, title, text)
        for i, e in enumerate(catalog):
            if e["_key"] == key:
                return i + 1
        merged = {
            "uri": convert_gs_to_authenticated_url(uri or (by_title.get(title) or {}).get("source_uri")),
            "title": title or (by_uri.get(uri) or {}).get("title"),
            "text": text,
            "score": None,
            "page_number": chunk.get("page_number"),
            "page_range": chunk.get("page_range"),
            "_key": key,
        }
        if merged["uri"] and merged["uri"] in by_uri:
            retrieved_item = by_uri[merged["uri"]]
            merged["title"] = merged["title"] or retrieved_item.get("title")
            merged["score"] = retrieved_item.get("score")
            merged["page_number"] = merged["page_number"] or retrieved_item.get("page_number")
            merged["page_range"] = merged["page_range"] or retrieved_item.get("page_range")
        elif merged["title"] and merged["title"] in by_title:
            retrieved_item = by_title[merged["title"]]
            merged["uri"] = merged["uri"] or retrieved_item.get("source_uri")
            merged["score"] = retrieved_item.get("score")
            merged["page_number"] = merged["page_number"] or retrieved_item.get("page_number")
            merged["page_range"] = merged["page_range"] or retrieved_item.get("page_range")
        catalog.append(merged)
        return len(catalog)

    for idx, ch in enumerate(gen_chunks or []):
        cite_num = ensure_entry(ch)
        index_to_cite_num[idx] = cite_num

    for e in catalog:
        e.pop("_key", None)

    return index_to_cite_num, catalog

def annotate_with_citations(text: str, supports: List[Dict[str, Any]], idx_to_num: Dict[int, int]) -> str:
    if not text or not supports:
        return text or ""
    def end_idx(s): 
        seg = s.get("segment") or {}
        return seg.get("end_index", 0)
    supports_sorted = sorted(supports, key=end_idx, reverse=True)
    out = text
    for s in supports_sorted:
        seg = s.get("segment") or {}
        end_i = seg.get("end_index")
        if end_i is None or end_i > len(out) or end_i < 0:
            continue
        idxs = s.get("grounding_chunk_indices") or []
        ids = [idx_to_num[i] for i in idxs if i in idx_to_num]
        if not ids:
            continue
        marker = "".join(f"[{n}]" for n in sorted(set(ids)))
        out = out[:end_i] + marker + out[end_i:]
    return out

def convert_gs_to_authenticated_url(gs_uri: str) -> str:
    """Convert gs:// URI to authenticated https:// URL"""
    if gs_uri and gs_uri.startswith('gs://'):
        # Convert gs://bucket/path to https://storage.cloud.google.com/bucket/path?authuser=0
        path = gs_uri.replace('gs://', '')
        return f'https://storage.cloud.google.com/{path}?authuser=0'
    return gs_uri

def render_sources_block(catalog: List[Dict[str, Any]]) -> str:
    if not catalog:
        return ""
    lines = ["", "---", "**Sources**", ""]
    for i, e in enumerate(catalog, start=1):
        title = e.get("title") or (e.get("uri") or "Source")
        uri = convert_gs_to_authenticated_url(e.get("uri") or "#")
        score = e.get("score")
        score_txt = f" — score: {score:.2f}" if isinstance(score, (int, float)) else ""
        lines.append(f"{i}. [{title}]({uri}){score_txt}")
    return "\n".join(lines)

# -----------------------------
# OAuth Routes
# -----------------------------

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('home'))
    
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return render_template('login.html', error="OAuth not configured")
    
    # If this is a GET request without start param, show login page
    if 'start' not in request.args:
        return render_template('login.html')
    
    try:
        # Start OAuth flow - ensure HTTPS for production
        redirect_uri = request.url_root.rstrip('/').replace('http://', 'https://') + '/login/callback'
        google = OAuth2Session(GOOGLE_CLIENT_ID, scope=["openid", "email", "profile"], redirect_uri=redirect_uri)
        authorization_url, state = google.authorization_url(AUTHORIZATION_BASE_URL, access_type="offline", prompt="select_account")
        session['oauth_state'] = state
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        return render_template('login.html', error="OAuth setup failed")

@app.route('/login/callback')
def callback():
    try:
        if 'oauth_state' not in session:
            logger.error("No oauth_state in session")
            return redirect(url_for('login'))
        
        redirect_uri = request.url_root.rstrip('/').replace('http://', 'https://') + '/login/callback'
        # Fix authorization_response URL to use HTTPS
        auth_response = request.url.replace('http://', 'https://')
        
        google = OAuth2Session(GOOGLE_CLIENT_ID, state=session['oauth_state'], redirect_uri=redirect_uri)
        token = google.fetch_token(TOKEN_URL, client_secret=GOOGLE_CLIENT_SECRET, authorization_response=auth_response)
        
        resp = google.get(USERINFO_URL)
        user_info = resp.json()
        
        session['user'] = {
            'id': user_info['sub'],
            'name': user_info['name'],
            'email': user_info['email'],
            'picture': user_info.get('picture')
        }
        
        return redirect(url_for('home'))
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# -----------------------------
# Routes
# -----------------------------

@app.get("/")
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", user=session.get('user'))

@app.get("/healthz")
def healthz():
    return jsonify(status="ok"), 200

@app.post("/clear")
@login_required
def clear_conversation():
    session.pop('conversation', None)
    return jsonify(status="cleared"), 200

@app.post("/chat")
@login_required
def chat():
    try:
        if not PROJECT_ID or not RAG_CORPUS:
            return jsonify(error="Server missing GOOGLE_CLOUD_PROJECT/PROJECT_ID or RAG_CORPUS_RESOURCE"), 500

        payload = request.get_json(silent=True) or {}
        user_msg = (payload.get("message") or "").strip()
        top_k = int(payload.get("top_k") or 5)
        if not user_msg:
            return jsonify(error="Please include a 'message' field."), 400

        # Get conversation history from session
        if 'conversation' not in session:
            session['conversation'] = []
        
        conversation_history = session['conversation'][-4:]  # Keep last 4 exchanges
        
        # Build conversation context
        context = ""
        if conversation_history:
            context = "\n\nPrevious conversation context:\n"
            for exchange in conversation_history:
                context += f"User: {exchange['user']}\nSystem: {exchange['bot']}\n"
        
        # Combine system prompt with context and current query
        full_prompt = f"{SYSTEM_PROMPT}{context}\n\nCurrent User Query: {user_msg}"
        
        retrieved = retrieve_contexts(user_msg, top_k=top_k)
        model = GenerativeModel(model_name=MODEL_NAME, tools=[build_rag_tool(top_k=top_k)])
        gen_response = model.generate_content(full_prompt)
        gen = extract_grounding_from_generation(gen_response)
        model_text = gen.get("text") or getattr(gen_response, "text", "") or ""

        idx_to_num, catalog = build_citation_catalog(gen.get("grounding_chunks", []), retrieved)
        annotated = annotate_with_citations(model_text, gen.get("grounding_supports", []), idx_to_num)
        sources_block = render_sources_block(catalog)
        response_markdown = annotated + sources_block

        # Store conversation in session
        session['conversation'].append({
            'user': user_msg,
            'bot': model_text[:200]  # Store truncated response
        })
        
        # Keep only last 5 exchanges
        if len(session['conversation']) > 5:
            session['conversation'] = session['conversation'][-5:]
        
        return jsonify({
            "response": model_text,
            "annotated_text": annotated,
            "response_markdown": response_markdown,
            "sources": catalog,
            "retrieved_contexts": retrieved
        })

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)