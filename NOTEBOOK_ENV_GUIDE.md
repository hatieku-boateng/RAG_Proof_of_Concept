# Notebook Cell Updates - Using Environment Variables

This document shows the corrected code for each cell in `openai_1.ipynb` that should use environment variables from `.env`

---

## Cell: "Uploading and Attaching file to vector store"

**Current Issue:** Hardcoded vector_store_id
**Solution:** Use environment variable

```python
# Load vector store ID from environment variable
vector_store_id = os.getenv("VECTOR_STORE_ID")

# Alternatively, use the vector_store object from the creation cell
# vector_store_id = vector_store.id

print(f"📦 Using Vector Store ID: {vector_store_id}")

# Upload file from course_outlines folder
file = client.files.create(
    file=open(
        "course_outlines/1.docx",
        "rb"
    ),
    purpose="assistants"
)

print(f"✅ File uploaded successfully!")
print(f"File ID: {file.id}")
print(f"Filename: {file.filename}")

# Attach file to vector store
vector_file = client.vector_stores.files.create(
    vector_store_id=vector_store_id,
    file_id=file.id
)

print(f"\n✅ File attached to vector store!")
print(f"Vector Store ID: {vector_store_id}")

# Check ingestion status
files = client.vector_stores.files.list(
    vector_store_id=vector_store_id
)

print("\n📋 Vector store file status:")
for f in files.data:
    print(f"  • File ID: {f.id} | Status: {f.status}")
```

---

## Cell: "Creating an OpenAI client"

**Current Code:** Already correct! ✅
**Verification:**

```python
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
model_chat = os.getenv("OPENAI_MODEL")
model_embedding = os.getenv("OPENAI_MODEL_EMBEDDING")

print(f'API Key loaded: {client.api_key[:5]}***')
print(f'Model loaded: {model_chat}')
print(f'Model embedding loaded: {model_embedding}')
```

---

## NEW Cell: "Loading Environment Variables Helper"

**Purpose:** Quick reference cell to show all loaded environment variables
**Add this as a new cell after loading libraries:**

```python
# Display all loaded environment variables (for reference)
print("="*60)
print("LOADED ENVIRONMENT VARIABLES")
print("="*60)
print(f"API Key: {os.getenv('OPENAI_API_KEY')[:15]}... (hidden)")
print(f"Chat Model: {os.getenv('OPENAI_MODEL')}")
print(f"Embedding Model: {os.getenv('OPENAI_MODEL_EMBEDDING')}")
print(f"Vector Store ID: {os.getenv('VECTOR_STORE_ID')}")
print("="*60)
```

---

## Cell: "Checking the number of files attached to vector store"

**Current Code:** Uses `vector_store.id` which is fine if running sequentially
**Improved Version:** Can also reference from environment

```python
# Option 1: Use the vector_store object from creation cell
files = client.vector_stores.files.list(vector_store_id=vector_store.id)

# Option 2: Use environment variable (useful if running cells independently)
# files = client.vector_stores.files.list(vector_store_id=os.getenv("VECTOR_STORE_ID"))

# Count and display
file_count = len(files.data)
print(f"Total files in vector store: {file_count}")

# Show details of each file
if file_count > 0:
    print("\nFile details:")
    for f in files.data:
        print(f"  - File ID: {f.id} | Status: {f.status}")
else:
    print("No files attached to this vector store.")
```

---

## Cell: "Searching the Vector Store"

**Add proper environment variable usage:**

```python
# Get vector store ID from environment or use the vector_store object
vector_store_id = os.getenv("VECTOR_STORE_ID")  # or vector_store.id

# Your search query
user_query = "What topics are covered in the course outline?"

print(f"🔍 Searching for: {user_query}\n")

# Use the Assistants API with file_search (RECOMMENDED METHOD)
assistant = client.beta.assistants.create(
    name="Course Outline Assistant",
    instructions="""You are an expert at analyzing educational course outlines.
    Provide detailed, accurate responses based on the course outline document.
    Always cite specific sections when answering questions.""",
    model=os.getenv("OPENAI_MODEL"),  # ✅ Using env variable
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [vector_store_id]
        }
    }
)

# Create thread and run
thread = client.beta.threads.create(
    messages=[{"role": "user", "content": user_query}]
)

run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id
)

# Display results
if run.status == 'completed':
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    
    for message in messages.data:
        if message.role == "assistant":
            for content in message.content:
                if content.type == 'text':
                    print("="*60)
                    print("🤖 ASSISTANT RESPONSE")
                    print("="*60)
                    print(content.text.value)
                    print("="*60)
    
    # Clean up
    client.beta.assistants.delete(assistant.id)
    print("\n✅ Search completed!")
else:
    print(f"❌ Search failed with status: {run.status}")
```

---

## Summary of Environment Variables in .env

```
OPENAI_API_KEY          - Your OpenAI API key
OPENAI_MODEL            - Model for chat/assistants (gpt-4o-mini)
OPENAI_MODEL_EMBEDDING  - Model for embeddings (text-embedding-3-small)
VECTOR_STORE_ID         - Your vector store ID for course outlines
```

---

## Best Practices

1. **Always use `os.getenv()`** for sensitive data like API keys
2. **Use environment variables** for IDs that might change across environments
3. **Keep models in .env** so you can easily switch between different models
4. **Never hardcode** API keys or IDs directly in notebooks
5. **Use the `vector_store` object** when running cells sequentially
6. **Use `os.getenv("VECTOR_STORE_ID")`** when running cells independently

---

## Quick Reference: How to Use in Any Cell

```python
# API Key
api_key = os.getenv("OPENAI_API_KEY")

# Models
chat_model = os.getenv("OPENAI_MODEL")
embedding_model = os.getenv("OPENAI_MODEL_EMBEDDING")

# Vector Store
vector_store_id = os.getenv("VECTOR_STORE_ID")
```

---

**Note:** Make sure to run the first cell that loads environment variables:
```python
from dotenv import load_dotenv
load_dotenv()
```
