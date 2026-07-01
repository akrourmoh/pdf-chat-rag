"""Central configuration for the PDF Chat application.

Every tunable setting lives here so it can be changed in one place instead of
being hard-coded across several files. Each value can also be overridden with an
environment variable, which is what lets us use different settings per
environment (local, staging, production) without touching the code.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file if one exists. On a server like Render
# there is no .env file - the variables are provided by the platform - so this
# call simply does nothing there.
load_dotenv()


# ── Environment ────────────────────────────────────────────────────────────────
# "development" (default) is lenient; "production" enforces secure settings.
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# ── API credentials ───────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ── Gemini models ──────────────────────────────────────────────────────────────
EMBED_MODEL = os.getenv("EMBED_MODEL", "gemini-embedding-001")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
# If the primary model is overloaded (503), we automatically fall back to this one.
LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "gemini-2.0-flash")

# ── Text chunking ──────────────────────────────────────────────────────────────
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))       # max characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))  # characters shared between chunks

# ── Retrieval ──────────────────────────────────────────────────────────────────
TOP_K = int(os.getenv("TOP_K", "6"))  # how many chunks to retrieve per question

# ── Performance ──────────────────────────────────────────────────────────────
# How many embedding requests to send in parallel (network-bound, so threads help).
EMBED_CONCURRENCY = int(os.getenv("EMBED_CONCURRENCY", "8"))
# How many recent embeddings to cache in memory (avoids repeat API calls).
EMBED_CACHE_SIZE = int(os.getenv("EMBED_CACHE_SIZE", "2048"))

# ── Vector database (Qdrant) ────────────────────────────────────────────────────
# If QDRANT_URL is set, we connect to a hosted Qdrant server (e.g. Qdrant Cloud)
# - this is what you use in production for real, shared persistence.
# If it is NOT set, we fall back to a local on-disk database stored at QDRANT_PATH,
# which needs no server and is perfect for local development.
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_PATH = os.getenv("QDRANT_PATH", "qdrant_data")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

# ── Backend API ──────────────────────────────────────────────────────────────
# The frontend calls the FastAPI backend at this address.
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Observability ────────────────────────────────────────────────────────────
# Optional: set SENTRY_DSN to send errors to Sentry (free tier available).
SENTRY_DSN = os.getenv("SENTRY_DSN")

# ── Database (users) ────────────────────────────────────────────────────────────
# SQLAlchemy connection string. The SAME code runs on either database:
#   - local dev:    sqlite:///users.db            (no server needed)
#   - production:   postgresql://user:pass@host:5432/dbname   (PostgreSQL)
# Just change this one environment variable - no code changes.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///users.db")

# ── Authentication (JWT) ────────────────────────────────────────────────────────
# JWT_SECRET signs the login tokens - it MUST be a long random value in
# production and must be kept secret (set it via an environment variable).
_DEV_JWT_SECRET = "dev-only-secret-change-me"
JWT_SECRET = os.getenv("JWT_SECRET", _DEV_JWT_SECRET)
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


# ── Configuration validation ────────────────────────────────────────────────────
def validate():
    # Check for missing or insecure settings. Returns (errors, warnings).
    # In production, errors should stop the app from starting (fail fast).
    errors, warnings = [], []
    is_prod = ENVIRONMENT == "production"

    if not GOOGLE_API_KEY:
        target = errors if is_prod else warnings
        target.append("GOOGLE_API_KEY is not set - the AI features will not work.")

    if JWT_SECRET == _DEV_JWT_SECRET:
        msg = "JWT_SECRET is using the insecure development default."
        (errors if is_prod else warnings).append(msg)

    if is_prod and DATABASE_URL.startswith("sqlite"):
        warnings.append("DATABASE_URL is SQLite; PostgreSQL is recommended in production.")

    return errors, warnings
