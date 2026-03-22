#!/usr/bin/env python3
# scripts/run_api.py — Start LEXSWARM FastAPI server
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn
from dotenv import load_dotenv
load_dotenv()
if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
