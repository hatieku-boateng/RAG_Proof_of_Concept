from pathlib import Path
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(override=True)

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Create a .env file with OPENAI_API_KEY=...")

vector_store_id = os.getenv("VECTOR_STORE_ID")
if not vector_store_id:
    raise RuntimeError("VECTOR_STORE_ID is not set. Update your .env with the 'Pentecost University Statute' vector store id.")

client = OpenAI(api_key=api_key)


FILE_PATHS = [
    # Optionally add one or more explicit paths to files you want to upload
    # Example: r"pu_repo\\pu_statute.pdf",
]

SOURCE_DIR = Path("pu_repo")

if not FILE_PATHS:
    # If no explicit paths are provided, default to uploading all files under pu_repo/
    if not SOURCE_DIR.exists() or not SOURCE_DIR.is_dir():
        raise FileNotFoundError(f"Directory not found: {SOURCE_DIR.resolve()}")

    FILE_PATHS = [str(p) for p in SOURCE_DIR.rglob("*") if p.is_file()]
    print(f"Auto-discovered {len(FILE_PATHS)} files under {SOURCE_DIR}")

if not FILE_PATHS:
    print("No files found to upload. Skipping upload.")
else:
    uploaded_file_ids: list[str] = []

    for p in FILE_PATHS:
        path = Path(p)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with path.open("rb") as file_data:
            f = client.files.create(file=file_data, purpose="assistants")

        client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=f.id)
        uploaded_file_ids.append(f.id)
        print(f"Uploaded and attached: {path.name} (file_id={f.id})")

    print(f"Total uploaded in this run: {len(uploaded_file_ids)}")