FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml .
RUN pip install httpx transformers torch langdetect fastapi uvicorn pydantic python-telegram-bot python-dotenv pyyaml loguru sentence-transformers --no-cache-dir
COPY . .
ENV PYTHONPATH=/app
CMD ["python", "scripts/run_api.py"]
