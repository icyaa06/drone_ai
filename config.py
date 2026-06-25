import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_env(path=BASE_DIR / ".env"):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env()


def normalize_database_uri(value):
    if not value:
        return value
    value = value.strip()
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://"):]
    if value.startswith("postgresql://"):
        value = "postgresql+psycopg2://" + value[len("postgresql://"):]
    return value


DATABASE_URI = normalize_database_uri(
    os.getenv("DATABASE_URI")
    or os.getenv("DATABASE_URL")
    or "postgresql+psycopg2://postgres:postgres@localhost/drone_ai_db"
)
SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change-me-drone-2026")
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "25")) * 1024 * 1024
UPLOAD_FOLDER = Path(os.getenv("UPLOAD_FOLDER", BASE_DIR / "uploads"))
ALLOWED_ORIGINS = [value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://127.0.0.1:5000,http://localhost:5000").split(",")]
