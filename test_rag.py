import os
from dotenv import load_dotenv
load_dotenv()

import vertexai
from vertexai import rag

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
LOCATION = os.environ.get("VERTEX_LOCATION", "us-central1")
RAG_CORPUS = os.environ.get("RAG_CORPUS_RESOURCE")

print(f"Project: {PROJECT_ID}")
print(f"Location: {LOCATION}")
print(f"RAG Corpus: {RAG_CORPUS}")

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    print("✅ Vertex AI initialized")
    
    # Test RAG query
    rag_retrieval_config = rag.RagRetrievalConfig(top_k=3)
    resp = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=RAG_CORPUS)],
        text="tobacco laws",
        rag_retrieval_config=rag_retrieval_config,
    )
    
    print("✅ RAG query successful")
    print(f"Response type: {type(resp)}")
    
    if hasattr(resp, 'contexts') and resp.contexts:
        contexts = resp.contexts.contexts
        print(f"Found {len(contexts)} contexts")
        for i, c in enumerate(contexts[:2]):
            print(f"\nContext {i+1}:")
            print(f"  Text: {getattr(c, 'text', 'No text')[:100]}...")
            print(f"  Title: {getattr(c, 'source_display_name', 'No title')}")
            print(f"  URI: {getattr(c, 'source_uri', 'No URI')}")
            print(f"  Distance: {getattr(c, 'distance', 'No distance')}")
            print(f"  Score: {getattr(c, 'score', 'No score')}")
            print(f"  All attributes: {[attr for attr in dir(c) if not attr.startswith('_')]}")
            
            # Check for metadata
            if hasattr(c, 'metadata'):
                metadata = getattr(c, 'metadata', {})
                print(f"  Metadata: {metadata}")
            
            # Check the chunk attribute for location info
            if hasattr(c, 'chunk'):
                chunk = getattr(c, 'chunk')
                print(f"  Chunk type: {type(chunk)}")
                print(f"  Chunk attributes: {[attr for attr in dir(chunk) if not attr.startswith('_')]}")
                
                # Check for common location attributes in chunk
                for attr in ['page_number', 'chunk_id', 'section', 'paragraph', 'metadata', 'page_span']:
                    if hasattr(chunk, attr):
                        value = getattr(chunk, attr)
                        print(f"  chunk.{attr}: {value}")
                        
                        # If it's page_span, inspect its attributes
                        if attr == 'page_span' and value:
                            print(f"    page_span type: {type(value)}")
                            print(f"    page_span attributes: {[a for a in dir(value) if not a.startswith('_')]}")
                            for span_attr in ['start_page', 'end_page', 'page_start', 'page_end']:
                                if hasattr(value, span_attr):
                                    print(f"    page_span.{span_attr}: {getattr(value, span_attr)}")
            
            # Check for other possible location attributes on context
            for attr in ['page_number', 'chunk_id', 'section', 'paragraph', 'page_span']:
                if hasattr(c, attr):
                    print(f"  {attr}: {getattr(c, attr)}")
    else:
        print("❌ No contexts found in response")
        print(f"Response attributes: {dir(resp)}")
        if hasattr(resp, 'contexts'):
            print(f"Contexts object: {resp.contexts}")
            print(f"Contexts attributes: {dir(resp.contexts)}")
        
except Exception as e:
    print(f"❌ Error: {e}")