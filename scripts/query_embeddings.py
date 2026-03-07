"""
Query saved embeddings using semantic search.
Useful for testing embeddings before importing to vector database.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from openai import OpenAI
import os

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=...")

client = OpenAI(api_key=api_key)

# Configuration
EMBEDDINGS_DIR = Path(__file__).parent.parent / "embeddings_output"
EMBEDDINGS_FILE = EMBEDDINGS_DIR / "embeddings.json"
EMBEDDING_MODEL = "text-embedding-3-small"


def load_embeddings(json_path: Path) -> List[Dict[str, Any]]:
    """Load embeddings from JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_query_embedding(query: str) -> List[float]:
    """Create embedding for a search query."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    )
    return response.data[0].embedding


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    return np.dot(a_arr, b_arr) / (np.linalg.norm(a_arr) * np.linalg.norm(b_arr))


def search_embeddings(
    query: str, 
    embeddings: List[Dict[str, Any]], 
    top_k: int = 5
) -> List[Tuple[Dict[str, Any], float]]:
    """Search embeddings for most similar chunks to query."""
    print(f"Creating query embedding for: '{query}'")
    query_embedding = create_query_embedding(query)
    
    # Calculate similarities
    results = []
    for item in embeddings:
        similarity = cosine_similarity(query_embedding, item['embedding'])
        results.append((item, similarity))
    
    # Sort by similarity (descending)
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:top_k]


def display_results(results: List[Tuple[Dict[str, Any], float]]):
    """Display search results."""
    print("\n" + "=" * 80)
    print("Search Results")
    print("=" * 80)
    
    for i, (item, similarity) in enumerate(results, 1):
        print(f"\n--- Result {i} (Similarity: {similarity:.4f}) ---")
        print(f"File: {item['file_name']}")
        print(f"Chunk: {item['chunk_index'] + 1}/{item['metadata']['total_chunks']}")
        print(f"\nText Preview:")
        text = item['chunk_text']
        # Show first 300 characters
        preview = text[:300] + "..." if len(text) > 300 else text
        print(preview)
        print("-" * 80)


def interactive_search(embeddings: List[Dict[str, Any]]):
    """Interactive search mode."""
    print("\n" + "=" * 80)
    print("Interactive Search Mode")
    print("=" * 80)
    print("Enter your query (or 'quit' to exit)")
    print("=" * 80)
    
    while True:
        query = input("\nQuery: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("Exiting...")
            break
        
        if not query:
            print("Please enter a query.")
            continue
        
        try:
            # Ask for number of results
            top_k_input = input("Number of results (default 5): ").strip()
            top_k = int(top_k_input) if top_k_input else 5
            
            # Search
            results = search_embeddings(query, embeddings, top_k=top_k)
            display_results(results)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    """Main function."""
    print("=" * 80)
    print("Query Embeddings")
    print("=" * 80)
    
    # Check if embeddings file exists
    if not EMBEDDINGS_FILE.exists():
        print(f"Error: Embeddings file not found: {EMBEDDINGS_FILE}")
        print("Please run create_embeddings.py first.")
        return
    
    # Load embeddings
    print(f"Loading embeddings from {EMBEDDINGS_FILE}...")
    embeddings = load_embeddings(EMBEDDINGS_FILE)
    print(f"Loaded {len(embeddings)} embeddings")
    
    # Example queries
    print("\n" + "=" * 80)
    print("Example Queries")
    print("=" * 80)
    
    example_queries = [
        "What are the admission requirements?",
        "Tell me about the university governance structure",
        "What is the academic calendar?"
    ]
    
    print("Running example queries:")
    for query in example_queries:
        print(f"\n>>> {query}")
        results = search_embeddings(query, embeddings, top_k=3)
        display_results(results)
        
        # Wait for user
        input("\nPress Enter to continue to next example query...")
    
    # Interactive mode
    try:
        interactive_search(embeddings)
    except KeyboardInterrupt:
        print("\n\nExiting...")


if __name__ == "__main__":
    main()
