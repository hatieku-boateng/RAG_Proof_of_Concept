
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


PROJECT_DIR = Path(__file__).resolve().parents[1]
PARENT_DIR = PROJECT_DIR.parent

ENV_PATH = PARENT_DIR / ".env"
if not ENV_PATH.exists():
    ENV_PATH = PROJECT_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=...")

vector_store_id = os.getenv("VECTOR_STORE_ID")
if not vector_store_id:
    raise RuntimeError("VECTOR_STORE_ID is not set. Update your .env with the 'Pentecost University Statute' vector store id.")

client = OpenAI(api_key=api_key)

print("=== Clearing files from vector store ===")

try:
    vs = client.vector_stores.retrieve(vector_store_id)
    print(f"Vector store: {vs.name} (id: {vs.id})")
except Exception:
    print(f"Vector store id: {vector_store_id}")

files_before = client.vector_stores.files.list(vector_store_id=vector_store_id)
print(f"Files before clear: {len(files_before.data)}")

if not files_before.data:
    print("No files to delete; vector store is already empty.")
else:
    for f in files_before.data:
        client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=f.id)
        print(f"Deleted file: {f.id} | status={getattr(f, 'status', 'unknown')}")

    files_after = client.vector_stores.files.list(vector_store_id=vector_store_id)
    print(f"Files after clear: {len(files_after.data)}")

print("Done.")

