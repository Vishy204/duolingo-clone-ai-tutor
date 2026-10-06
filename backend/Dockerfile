FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    NLTK_DATA=/usr/share/nltk_data

WORKDIR /app

# libgomp is needed by onnxruntime (Silero VAD for the voice pipeline)
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && python -m nltk.downloader -d /usr/share/nltk_data punkt_tab

COPY app ./app

# Run as an unprivileged user; the SQLite file lives in /app/data
RUN useradd --create-home appuser && mkdir -p /app/data && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*' --no-access-log"]
