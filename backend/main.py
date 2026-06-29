"""
Learning Companion — FastAPI Backend
Run with: uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os

load_dotenv()

from backend.routes import study, ask, quiz, improve, forget, graph

app = FastAPI(
    title="Learning Companion API",
    description="Persistent AI study assistant powered by Cognee memory.",
    version="1.0.0",
)

# Allow frontend (served from /frontend or any origin during dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(study.router)
app.include_router(ask.router)
app.include_router(quiz.router)
app.include_router(improve.router)
app.include_router(forget.router)
app.include_router(graph.router)

# Serve frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


@app.get("/health")
async def health():
    return {"status": "ok"}
