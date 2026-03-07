# Embeddings Scripts

This directory contains scripts to create, export, and query embeddings from files in the `pu_repo` directory.

## Scripts Overview

### 1. `create_embeddings.py`
Creates embeddings for all files in the `pu_repo` directory using OpenAI's embedding API.

**Features:**
- Supports PDF, TXT, MD, PY, JS, HTML, CSS, JSON, and XML files
- Chunks large files into manageable pieces with overlap
- Creates embeddings using `text-embedding-3-small` model (configurable)
- Saves embeddings to JSON format in `embeddings_output/embeddings.json`

**Usage:**
```bash
python scripts/create_embeddings.py
```

**Configuration:**
- `CHUNK_SIZE`: 1000 characters per chunk (default)
- `CHUNK_OVERLAP`: 200 characters overlap between chunks
- `EMBEDDING_MODEL`: "text-embedding-3-small" (or "text-embedding-3-large")

### 2. `export_embeddings_to_csv.py`
Exports embeddings from JSON to CSV and Parquet formats for easier import into vector databases.

**Features:**
- Converts JSON embeddings to CSV format
- Converts JSON embeddings to Parquet format (more efficient)
- Displays statistics about embeddings

**Usage:**
```bash
python scripts/export_embeddings_to_csv.py
```

**Output Files:**
- `embeddings_output/embeddings.csv` - CSV format
- `embeddings_output/embeddings.parquet` - Parquet format (recommended for large datasets)

### 3. `query_embeddings.py`
Test and query the saved embeddings using semantic search before importing to a vector database.

**Features:**
- Search embeddings using natural language queries
- Interactive query mode
- Example queries included
- Displays similarity scores and text previews

**Usage:**
```bash
python scripts/query_embeddings.py
```

## Workflow

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

3. **Create embeddings:**
   ```bash
   python scripts/create_embeddings.py
   ```
   This will process all files in `pu_repo/` and save embeddings to `embeddings_output/embeddings.json`

4. **Export to CSV/Parquet (optional):**
   ```bash
   python scripts/export_embeddings_to_csv.py
   ```
   This converts the JSON format to CSV and Parquet for easier import into vector databases.

5. **Test embeddings (optional):**
   ```bash
   python scripts/query_embeddings.py
   ```
   This lets you test semantic search on your embeddings before importing to a database.

## Output Format

### JSON Format (`embeddings.json`)
```json
[
  {
    "file_name": "pu_statute.pdf",
    "file_path": "pu_repo/pu_statute.pdf",
    "chunk_index": 0,
    "chunk_text": "Content of the chunk...",
    "embedding": [0.123, -0.456, ...],
    "metadata": {
      "total_chunks": 10,
      "chunk_size": 1000,
      "model": "text-embedding-3-small"
    }
  }
]
```

### CSV Format
Columns: `file_name`, `file_path`, `chunk_index`, `chunk_text`, `embedding`, `total_chunks`, `chunk_size`, `model`

### Parquet Format
Same structure as CSV but in efficient binary format, ideal for large datasets.

## Importing to Vector Databases

### Pinecone
```python
import pinecone
import json

# Load embeddings
with open('embeddings_output/embeddings.json', 'r') as f:
    embeddings = json.load(f)

# Initialize Pinecone
pinecone.init(api_key='your_key', environment='your_env')
index = pinecone.Index('your_index')

# Upsert embeddings
for item in embeddings:
    index.upsert([(
        f"{item['file_name']}_{item['chunk_index']}",
        item['embedding'],
        {
            'file_name': item['file_name'],
            'chunk_text': item['chunk_text']
        }
    )])
```

### Weaviate
```python
import weaviate
import json

# Load embeddings
with open('embeddings_output/embeddings.json', 'r') as f:
    embeddings = json.load(f)

client = weaviate.Client("http://localhost:8080")

# Import data
for item in embeddings:
    client.data_object.create(
        {
            'file_name': item['file_name'],
            'chunk_text': item['chunk_text']
        },
        'Document',
        vector=item['embedding']
    )
```

### Chroma
```python
import chromadb
import json

# Load embeddings
with open('embeddings_output/embeddings.json', 'r') as f:
    embeddings = json.load(f)

client = chromadb.Client()
collection = client.create_collection("pu_documents")

# Add embeddings
collection.add(
    embeddings=[item['embedding'] for item in embeddings],
    documents=[item['chunk_text'] for item in embeddings],
    metadatas=[{'file_name': item['file_name']} for item in embeddings],
    ids=[f"{item['file_name']}_{item['chunk_index']}" for item in embeddings]
)
```

## Notes

- The scripts automatically handle PDF text extraction
- Text chunking uses intelligent boundary detection (paragraphs, sentences)
- Embeddings are created using OpenAI's API (costs apply based on token usage)
- The `text-embedding-3-small` model provides good quality at lower cost
- For higher quality, change `EMBEDDING_MODEL` to `text-embedding-3-large` in the scripts

## Troubleshooting

**Issue:** "OPENAI_API_KEY is not set"
- Create a `.env` file in the project root with your API key

**Issue:** "No text extracted from PDF"
- Some PDFs may be image-based. Consider using OCR tools like `pytesseract` for these cases

**Issue:** File size too large
- Use the Parquet export format for more efficient storage
- Consider increasing `CHUNK_SIZE` to create fewer, larger chunks
