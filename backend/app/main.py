"""App entry point: CORS, routers, health check and JSON error handlers."""
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, authors, admin

logging.basicConfig(level=logging.INFO)

# tables only, seeding is a separate step (app/seed.py)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BookLeaf Author Support & Communication Portal",
    version="1.0.0",
    description="Author and admin support portal with Gemini-assisted ticket triage and reply drafting.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# error handlers

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


app.include_router(auth.router)
app.include_router(authors.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["meta"])
def health():
    """for docker/cloud run healthchecks, also shows whether the AI key was picked up"""
    return {"status": "ok", "ai_active": settings.ai_active, "model": settings.ai_model}


# the root Dockerfile copies the built frontend to backend/static, so one container serves both
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def frontend(path: str):
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        file = (STATIC_DIR / path).resolve()
        if path and file.is_file() and STATIC_DIR in file.parents:
            return FileResponse(file)
        return FileResponse(STATIC_DIR / "index.html")
