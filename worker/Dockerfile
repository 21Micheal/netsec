# Network Security Automation Worker Dockerfile
# This is a standalone RQ worker - the main Celery worker is in backend/Dockerfile.worker
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for security tools and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    nmap \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /worker

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . .

# Run the RQ worker
CMD ["python", "-u", "worker.py"]