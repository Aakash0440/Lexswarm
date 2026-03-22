import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LEXSWARM Legal Defense API",
    description="AI legal defense for 5 billion unrepresented people",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from api.routes import cases, documents, health
    app.include_router(health.router)
    app.include_router(cases.router, prefix="/cases")
    app.include_router(documents.router, prefix="/documents")
except Exception as e:
    print(f"[API] Route warning: {e}")

from api.routes.auth import router as auth_router
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "LEXSWARM API running", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "lexswarm-api"}