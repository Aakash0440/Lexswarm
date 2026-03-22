FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu --no-cache-dir
RUN pip install httpx transformers langdetect fastapi uvicorn pydantic python-telegram-bot python-dotenv pyyaml loguru sentence-transformers supabase==2.28.3 --no-cache-dir

COPY . .
ENV PYTHONPATH=/app
CMD ["python", "scripts/run_api.py"]