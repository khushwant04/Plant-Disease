# Backend API (FastAPI + PyTorch). The Next.js frontend in frontend/ is run separately.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# CPU-only PyTorch wheels keep the image much smaller than the default CUDA build.
COPY requirements.txt .
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser model/ ./model/

USER appuser

# Class names are read from the sub-folder names of $DATASET_PATH; mount it at runtime.
ENV DATASET_PATH=/app/Plantdisease/train

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
