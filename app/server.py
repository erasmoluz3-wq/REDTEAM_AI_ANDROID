import hmac
import os
import sys
import threading
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Usa os módulos originais do projeto, sem copiá-los ou substituí-los.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ROOT = PROJECT_ROOT / "app" / "src" / "main" / "python"
STATIC_ROOT = Path(__file__).resolve().parent / "static"

sys.path.insert(0, str(PYTHON_ROOT))

from core.brain import Brain  # noqa: E402

app = FastAPI(
    title="REDTEAM AI",
    version="1.0.0",
    docs_url=None,
    redoc_url=None
)

_brain = None
_lock = threading.RLock()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)


def get_brain():
    global _brain

    with _lock:
        if _brain is None:
            _brain = Brain()
        return _brain


def verify_token(authorization: str | None):
    expected = os.getenv("REDTEAM_API_TOKEN")

    if not expected:
        raise HTTPException(
            status_code=503,
            detail="REDTEAM_API_TOKEN não configurado no servidor."
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Autenticação necessária."
        )

    supplied = authorization[7:].strip()

    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=401,
            detail="Token inválido."
        )


@app.get("/")
def home():
    index = STATIC_ROOT / "index.html"

    if not index.is_file():
        raise HTTPException(status_code=404, detail="Interface não encontrada.")

    return FileResponse(index)


@app.get("/health")
def health():
    return {"service": "REDTEAM AI", "status": "online"}


@app.post("/api/chat")
def chat(
    payload: ChatRequest,
    authorization: str | None = Header(default=None)
):
    verify_token(authorization)

    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=422, detail="Pergunta vazia.")

    with _lock:
        answer = get_brain().ask(question)

    return {"answer": answer}


@app.get("/api/status")
def status(authorization: str | None = Header(default=None)):
    verify_token(authorization)

    with _lock:
        return get_brain().status()
