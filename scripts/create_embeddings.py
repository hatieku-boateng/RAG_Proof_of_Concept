"""
Create embeddings for files in pu_repo directory.
Saves embeddings to JSON file for later export to vector database.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI
import PyPDF2

# Load environment variables
load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=...")

client = OpenAI(api_key=api_key)

# Configuration
PU_REPO_DIR = Path(__file__).parent.parent / "pu_repo"
OUTPUT_DIR = Path(__file__).parent.parent / "embeddings_output"
EMBEDDING_MODEL = "text-embedding-3-small"  # or "text-embedding-3-large" for higher quality
CHUNK_SIZE = 1000  # characters per chunk
CHUNK_OVERLAP = 200  # overlap between chunks


def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    text = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num + 1}: {e}")
    return text


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from various file types."""
    suffix = file_path.suffix.lower()
    
    if suffix == '.pdf':
        return extract_text_from_pdf(file_path)
    elif suffix in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml']:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        print(f"Warning: Unsupported file type {suffix} for {file_path}")
        return ""


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at a sentence or paragraph boundary
        if end < len(text):
            # Look for sentence endings
            for delimiter in ['\n\n', '\n', '. ', '! ', '? ']:
                last_delimiter = text[start:end].rfind(delimiter)
                if last_delimiter != -1:
                    end = start + last_delimiter + len(delimiter)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def create_embedding(text: str) -> List[float]:
    """Create embedding for a text chunk using OpenAI API."""
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error creating embedding: {e}")
        raise


def process_file(file_path: Path) -> List[Dict[str, Any]]:
    """Process a single file and create embeddings for its chunks."""
    print(f"Processing: {file_path.name}")
    
    # Extract text
    text = extract_text_from_file(file_path)
    if not text.strip():
        print(f"  No text extracted from {file_path.name}")
        return []
    
    print(f"  Extracted {len(text)} characters")
    
    # Chunk text
    chunks = chunk_text(text)
    print(f"  Created {len(chunks)} chunks")
    
    # Create embeddings
    embeddings_data = []
    for i, chunk in enumerate(chunks):
        print(f"  Creating embedding for chunk {i+1}/{len(chunks)}")
        embedding = create_embedding(chunk)
        
        embeddings_data.append({
            "file_name": file_path.name,
            "file_path": str(file_path.relative_to(PU_REPO_DIR.parent)),
            "chunk_index": i,
            "chunk_text": chunk,
            "embedding": embedding,
            "metadata": {
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "model": EMBEDDING_MODEL
            }
        })
    
    return embeddings_data


def process_directory(directory: Path) -> List[Dict[str, Any]]:
    """Process all files in a directory."""
    all_embeddings = []
    
    # Find all files (recursively)
    files = [f for f in directory.rglob('*') if f.is_file()]
    print(f"Found {len(files)} files in {directory}")
    
    for file_path in files:
        try:
            embeddings = process_file(file_path)
            all_embeddings.extend(embeddings)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return all_embeddings


def save_embeddings(embeddings: List[Dict[str, Any]], output_path: Path):
    """Save embeddings to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(embeddings, f, indent=2)
    
    print(f"\nSaved {len(embeddings)} embeddings to {output_path}")
    
    # Calculate and display file size
    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Output file size: {size_mb:.2f} MB")


def main():
    """Main function to create embeddings for all files in pu_repo."""
    print("=" * 60)
    print("Creating Embeddings for PU Repo Files")
    print("=" * 60)
    print(f"Source directory: {PU_REPO_DIR}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Chunk size: {CHUNK_SIZE} characters")
    print(f"Chunk overlap: {CHUNK_OVERLAP} characters")
    print("=" * 60)
    
    # Check if source directory exists
    if not PU_REPO_DIR.exists():
        raise FileNotFoundError(f"Directory not found: {PU_REPO_DIR}")
    
    # Process all files
    embeddings = process_directory(PU_REPO_DIR)
    
    if not embeddings:
        print("\nNo embeddings created. Check if there are supported files in the directory.")
        return
    
    # Save embeddings
    output_path = OUTPUT_DIR / "embeddings.json"
    save_embeddings(embeddings, output_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total embeddings created: {len(embeddings)}")
    print(f"Output file: {output_path}")
    
    # Count by file
    files_processed = set(e["file_name"] for e in embeddings)
    print(f"Files processed: {len(files_processed)}")
    for file_name in sorted(files_processed):
        count = sum(1 for e in embeddings if e["file_name"] == file_name)
        print(f"  - {file_name}: {count} chunks")


if __name__ == "__main__":
    main()
