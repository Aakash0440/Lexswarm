# api/main.py — CORS-enabled FastAPI for Railway deployment
# Replace your existing api/main.py with this file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="LEXSWARM API",
    description="AI Legal Defense System",
    version="1.0.0"
)

# ── CORS — allows your Vercel frontend to call this API ──────────────────────
# Add your Vercel URL here after deploying the frontend
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    # Paste your Vercel URL below (e.g. "https://lexswarm-abc123.vercel.app")
    os.getenv("FRONTEND_URL", "*"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Change to ALLOWED_ORIGINS after you know your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
try:
    from api.routes import cases, documents, health
    app.include_router(health.router, tags=["health"])
    app.include_router(cases.router, prefix="/cases", tags=["cases"])
    app.include_router(documents.router, prefix="/documents", tags=["documents"])
except Exception as e:
    print(f"[API] Warning: could not load all routes: {e}")

@app.get("/")
def root():
    return {
        "status": "LEXSWARM API running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "lexswarm-api"}
