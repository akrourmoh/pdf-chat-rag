"""FastAPI backend for the PDF Chat application.

Public endpoints:
  GET  /health    - simple health check
  POST /register  - create an account (email + password)
  POST /login     - log in, returns a JWT access token

Protected endpoints (require a valid token):
  GET  /me        - the current logged-in user
  GET  /status    - whether documents are ready to query
  POST /process   - upload one or more PDFs to be processed and stored
  POST /ask       - ask a question, returns an answer with its sources

The frontend (static HTML/CSS/JS) talks to this API over HTTP/JSON.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

import config
import observability
from observability import request_id_var
from rag import service
from gemini_client import GeminiError
from db.database import get_db, init_db
from db.models import User
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)

logger = logging.getLogger("pdfchat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up logging + optional error tracking before anything else.
    observability.configure_logging()
    observability.init_error_tracking()

    # Validate configuration before serving. In production, missing/insecure
    # secrets stop the app from starting (fail fast); in development we only warn.
    errors, warnings = config.validate()
    for warning in warnings:
        logger.warning("Config warning: %s", warning)
    if errors:
        raise RuntimeError(
            "Cannot start - fix these configuration problems:\n- "
            + "\n- ".join(errors)
        )

    # Create database tables (if needed) when the API starts up.
    init_db()
    yield


app = FastAPI(title="PDF Chat API", version="1.0.0", lifespan=lifespan)

# Allow the browser frontend to call this API. In production you would restrict
# allow_origins to your actual frontend domain instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Give each request a short id, time it, and log the outcome.
    rid = uuid.uuid4().hex[:8]
    request_id_var.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception(
            "%s %s -> error (%.0fms)", request.method, request.url.path, elapsed
        )
        raise
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %s (%.0fms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    response.headers["X-Request-ID"] = rid
    return response


# ── Request / response models ───────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: EmailStr


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: list[str]


# ── Frontend (static HTML/CSS/JS) ────────────────────────────────────────────
# Serve the browser frontend: the login page at "/" and the chat page at "/chat".
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.get("/", include_in_schema=False)
def serve_login():
    return FileResponse("frontend/index.html")


@app.get("/chat", include_in_schema=False)
def serve_chat():
    return FileResponse("frontend/chat.html")


# ── Public endpoints ─────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register", response_model=UserResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    # Reject duplicate emails and too-short passwords.
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="This email is already registered.")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    user = User(email=request.email, hashed_password=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(id=user.id, email=user.email)


@app.post("/login", response_model=TokenResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2 form sends the email in the "username" field.
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


# ── Protected endpoints ──────────────────────────────────────────────────────
@app.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)


@app.get("/status")
def status_endpoint(current_user: User = Depends(get_current_user)):
    return {"documents_ready": service.documents_ready(current_user.id)}


@app.post("/process")
async def process(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    items = []
    for upload in files:
        content = await upload.read()
        items.append((upload.filename, content))

    if not items:
        raise HTTPException(status_code=400, detail="No files were uploaded.")

    try:
        chunk_count = service.process_documents(items, current_user.id)
    except GeminiError as exc:
        logger.warning("Gemini unavailable while processing for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=503, detail="The AI service is temporarily unavailable.")
    except Exception:
        logger.exception("Failed to process uploads for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to process the uploaded files.")

    return {"chunks": chunk_count, "files": len(items)}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest, current_user: User = Depends(get_current_user)):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="The question must not be empty.")

    if not service.documents_ready(current_user.id):
        raise HTTPException(status_code=400, detail="No documents have been processed yet.")

    try:
        answer, sources = service.answer_question(question, current_user.id)
    except GeminiError as exc:
        logger.warning("Gemini unavailable while answering for user %s: %s", current_user.id, exc)
        raise HTTPException(status_code=503, detail="The AI service is temporarily unavailable.")
    except Exception:
        logger.exception("Failed to answer question for user %s", current_user.id)
        raise HTTPException(status_code=500, detail="Failed to answer the question.")

    return AskResponse(answer=answer, sources=sources)
