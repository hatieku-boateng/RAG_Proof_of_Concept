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

client = OpenAI(api_key=api_key)


def main() -> None:
    """List all vector stores in the account and print a summary."""
    try:
        stores = client.vector_stores.list(limit=100)
    except Exception as e:
        print(f"Error listing vector stores: {e}")
        return

    data = getattr(stores, "data", [])
    count = len(data)

    print(f"Total vector stores: {count}")

    if not data:
        print("No vector stores found in this account.")
        return

    print("\nVector stores:")
    for vs in data:
        vs_id = getattr(vs, "id", "<unknown-id>")
        name = getattr(vs, "name", "<no-name>")
        status = getattr(vs, "status", "<unknown>")
        print(f"- {vs_id} | name={name} | status={status}")


if __name__ == "__main__":
    main()

