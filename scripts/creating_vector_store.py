### Creating a vector store

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

vector_store_id_env = os.getenv("VECTOR_STORE_ID")
client = OpenAI(api_key=api_key)


def create_or_get_vector_store(name: str, description: str | None = None):
    """Create a vector store by name, or return an existing one if it already exists."""
    if not name.strip():
        raise ValueError("Vector store name must be non-empty")

    stores = client.vector_stores.list(limit=100)
    for vs in stores.data:
        if vs.name == name:
            print("Vector store already exists:")
            print(f"  Name: {vs.name}")
            print(f"  ID:   {vs.id}")
            return vs

    vs = client.vector_stores.create(name=name, description=description)
    print("Vector store created:")
    print(f"  Name: {vs.name}")
    print(f"  ID:   {vs.id}")
    return vs


VECTOR_STORE_NAME = "Pentecost University Statute"
VECTOR_STORE_DESCRIPTION = "Pentecost University Statute knowledge base"

vector_store = None

# Prefer an explicit VECTOR_STORE_ID from the environment only if it actually
# points to the expected store name ("Pentecost University Statute"). Otherwise, fall back to
# creating or retrieving by name so we always end up on the right store.
if vector_store_id_env:
    try:
        existing = client.vector_stores.retrieve(vector_store_id_env)
        if existing.name == VECTOR_STORE_NAME:
            vector_store = existing
            print("Using existing vector store from .env")
            print(f"  Name: {existing.name}")
            print(f"  ID:   {existing.id}")
        else:
            print(
                "VECTOR_STORE_ID from env points to a different store "
                f"('{existing.name}'); expected '{VECTOR_STORE_NAME}'. Ignoring env value."
            )
    except Exception as e:
        print(f"Could not retrieve VECTOR_STORE_ID from env ({vector_store_id_env}): {e}")

if vector_store is None:
    vector_store = create_or_get_vector_store(
        name=VECTOR_STORE_NAME,
        description=VECTOR_STORE_DESCRIPTION,
    )

vector_store_id = vector_store.id
print(f"Using vector store '{VECTOR_STORE_NAME}' with id: {vector_store_id}")