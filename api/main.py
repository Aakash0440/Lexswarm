# api/main.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import cases, documents, health

app = FastAPI(
    title="LEXSWARM Legal Defense API",
    description="AI legal defense for 5 billion unrepresented people",
    version="1.0.0",
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(cases.router,     prefix="/cases")
app.include_router(documents.router, prefix="/documents")

@app.get("/")
async def root():
    return {
        "name": "LEXSWARM",
        "version": "1.0.0",
        "mission": "AI legal defense for the unrepresented",
        "endpoints": ["/cases/analyze", "/cases/{id}", "/documents/{case_id}", "/health"],
    }
