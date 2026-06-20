FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] google-genai

COPY ai_service ./ai_service

EXPOSE 8001

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
