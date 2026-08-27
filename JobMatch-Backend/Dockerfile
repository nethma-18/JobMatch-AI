# Production Dockerfile for JobMatch AI Backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Poppler & Tesseract for PDF/OCR handling)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy English model
RUN python -m spacy download en_core_web_sm

# Copy application source code
COPY . .

# Create upload and model directories
RUN mkdir -p uploads/resumes uploads/job_descriptions data/models data/datasets

EXPOSE 8000

# Production Uvicorn command with 4 worker processes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
