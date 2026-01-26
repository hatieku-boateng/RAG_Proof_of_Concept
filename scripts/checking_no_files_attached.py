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


try:
    vs = client.vector_stores.retrieve(vector_store_id)
    print(f"Vector store: {vs.name} (id: {vs.id})")
except Exception:
    vs = None
    print(f"Vector store id: {vector_store_id}")

files = client.vector_stores.files.list(vector_store_id=vector_store_id)
print(f"Total files in vector store: {len(files.data)}")

if not files.data:
    print("No files are currently attached to this vector store.")
else:
    for f in files.data:
        print(f"{f.id} | status={f.status}")
