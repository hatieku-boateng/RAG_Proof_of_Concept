from pathlib import Path
import os
from datetime import datetime, timezone

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


def _infer_classification(path: Path) -> str:
    env_classification = (os.getenv("DOCUMENT_CLASSIFICATION") or "").strip().lower()
    if env_classification:
        if env_classification not in {"public", "student", "staff", "admin"}:
            raise ValueError(
                "DOCUMENT_CLASSIFICATION must be one of: public, student, staff, admin "
                f"(got: {env_classification})"
            )
        return env_classification

    # Infer from folder name (e.g., pu_repo/public/..., pu_repo/student/..., etc.)
    lowered_parts = [p.lower() for p in path.parts]
    for c in ("public", "student", "staff", "admin"):
        if c in lowered_parts:
            return c

    return "public"


def _parse_semicolon_map(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    raw = (raw or "").strip()
    if not raw:
        return out
    for entry in raw.split(";"):
        entry = entry.strip()
        if not entry or "=" not in entry:
            continue
        k, v = entry.split("=", 1)
        k = k.strip()
        v = v.strip()
        if k and v:
            out[k] = v
    return out


def _get_file_env_key(path: Path) -> str | None:
    mapping = _parse_semicolon_map(os.getenv("FILE_ENV_KEY_MAP") or "")
    return mapping.get(path.name)


def _build_attributes(path: Path) -> dict:
    file_key = _get_file_env_key(path)

    version = (os.getenv("DOCUMENT_VERSION") or "").strip()
    source = (os.getenv("DOCUMENT_SOURCE") or "pu_repo").strip() or "pu_repo"
    view_source_url = (os.getenv("VIEW_SOURCE_URL") or "").strip()

    # Backwards-compatible fallbacks
    source_url = (os.getenv("DOCUMENT_SOURCE_URL") or "").strip()

    if file_key:
        per_source = (os.getenv(f"DOCUMENT_SOURCE_{file_key}") or "").strip()
        if per_source:
            source = per_source

        per_version = (os.getenv(f"DOCUMENT_VERSION_{file_key}") or "").strip()
        if per_version:
            version = per_version

        per_class = (os.getenv(f"DOCUMENT_CLASSIFICATION_{file_key}") or "").strip().lower()
        if per_class:
            if per_class not in {"public", "student", "staff", "admin"}:
                raise ValueError(
                    f"DOCUMENT_CLASSIFICATION_{file_key} must be one of: public, student, staff, admin "
                    f"(got: {per_class})"
                )
            classification = per_class
        else:
            classification = _infer_classification(path)

        per_view_url = (os.getenv(f"VIEW_SOURCE_URL_{file_key}") or "").strip()
        if per_view_url:
            view_source_url = per_view_url

        per_url = (os.getenv(f"DOCUMENT_SOURCE_URL_{file_key}") or "").strip()
        if per_url:
            source_url = per_url
    else:
        classification = _infer_classification(path)

    # Support map-style env vars (filename=url) as a secondary option.
    view_map = _parse_semicolon_map(os.getenv("VIEW_SOURCE_URLS") or "")
    if path.name in view_map:
        view_source_url = view_map[path.name]

    src_map = _parse_semicolon_map(os.getenv("DOCUMENT_SOURCE_URLS") or "")
    if path.name in src_map:
        source_url = src_map[path.name]

    if not view_source_url:
        view_source_url = source_url

    try:
        username = os.getlogin()
    except Exception:
        username = None

    return {
        "doc": path.stem,
        "version": version or None,
        "classification": classification,
        "source": source,
        "view_source_url": view_source_url or None,
        "source_url": source_url or None,
        "path": str(path.as_posix()),
        "retrieval_ingested_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_ingested_by": username,
        "retrieval_pipeline": "uploading_file_toVS.py",
    }


FILE_PATHS = [
    # Optionally add one or more explicit paths to files you want to upload
    # Example: r"pu_repo\\pu_statute.pdf",
]

SOURCE_DIR = PROJECT_DIR / "pu_repo"

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

        attributes = _build_attributes(path)

        # Attach to vector store with metadata if supported by the API; fall back otherwise.
        try:
            client.vector_stores.files.create(
                vector_store_id=vector_store_id,
                file_id=f.id,
                attributes=attributes,
            )
        except TypeError:
            client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=f.id)
        except Exception:
            client.vector_stores.files.create(vector_store_id=vector_store_id, file_id=f.id)
        uploaded_file_ids.append(f.id)
        print(f"Uploaded and attached: {path.name} (file_id={f.id})")

    print(f"Total uploaded in this run: {len(uploaded_file_ids)}")