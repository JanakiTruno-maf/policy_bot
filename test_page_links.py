import os
from dotenv import load_dotenv
load_dotenv()

import vertexai
from vertexai import rag

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
RAG_CORPUS = os.environ.get("RAG_CORPUS_RESOURCE")

def convert_gs_to_authenticated_url(gs_uri: str) -> str:
    """Convert gs:// URI to authenticated https:// URL"""
    if gs_uri and gs_uri.startswith('gs://'):
        path = gs_uri.replace('gs://', '')
        return f'https://storage.cloud.google.com/{path}?authuser=0'
    return gs_uri

def test_rag_with_pages():
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    # Test query about tobacco laws
    query = "What are the advertising restrictions for tobacco products in Poland?"
    
    rag_retrieval_config = rag.RagRetrievalConfig(top_k=3)
    resp = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
        text=query,
        rag_retrieval_config=rag_retrieval_config,
    )
    
    print(f"Query: {query}")
    print("="*60)
    
    if hasattr(resp, 'contexts') and resp.contexts:
        contexts = resp.contexts.contexts
        print(f"Found {len(contexts)} contexts\n")
        
        for i, c in enumerate(contexts, 1):
            print(f"Source {i}:")
            
            # Basic info
            title = getattr(c, 'source_display_name', 'Unknown')
            uri = getattr(c, 'source_uri', '')
            score = getattr(c, 'score', 0)
            text = getattr(c, 'text', '')[:200] + "..."
            
            print(f"  Title: {title}")
            print(f"  URI: {uri}")
            print(f"  Score: {score:.3f}")
            
            # Page information
            chunk = getattr(c, "chunk", None)
            if chunk and hasattr(chunk, "page_span"):
                page_span = getattr(chunk, "page_span")
                if page_span:
                    first_page = getattr(page_span, "first_page", None)
                    last_page = getattr(page_span, "last_page", None)
                    if first_page:
                        if last_page and last_page != first_page:
                            page_info = f"Pages {first_page}-{last_page}"
                        else:
                            page_info = f"Page {first_page}"
                        print(f"  Location: {page_info}")
                        
                        # Create the link with page fragment
                        auth_url = convert_gs_to_authenticated_url(uri)
                        page_link = f"{auth_url}#page={first_page}"
                        print(f"  Direct Link: {page_link}")
            
            print(f"  Text Preview: {text}")
            print("-" * 40)
    
    else:
        print("No contexts found")

if __name__ == "__main__":
    test_rag_with_pages()