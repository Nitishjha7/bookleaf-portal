"""
FastAPI application entry point.

Wires together CORS, the routers, a health check, and a couple of global
exception handlers so clients always get a clean JSON error (never a bare 500).
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, authors, admin

logging.basicConfig(level=logging.INFO)

# Create tables on boot if they don't exist. (Seeding is a separate explicit
# step — see app/seed.py — so we never wipe data automatically.)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BookLeaf Author Support & Communication Portal",
    version="1.0.0",
    description=(
        "Two-portal support system (author + admin) with AI-assisted ticket "
        "triage and reply drafting. See the README for architecture and the "
        "AI integration strategy."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- global error handling (requirement C: meaningful errors, not 500s) ---

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request data", "errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


# --- routes ---------------------------------------------------------------

app.include_router(auth.router)
app.include_router(authors.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["meta"])
def health():
    """Liveness probe + a quick way to confirm whether AI is configured."""
    return {"status": "ok", "ai_active": settings.ai_active, "model": settings.ai_model}
