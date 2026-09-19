# ==============================================================================
# SDOC Hackathon — Local Server (Docker)
# Specification Reference: Page 3 & 4 of Shipping Document Verification Use Case
# Run: docker compose up --build
# Access HTTP at http://localhost:8080
# ==============================================================================
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and data assets
COPY backend/ /app/backend/
COPY "test data/" "/app/test data/"
COPY tests/ /app/tests/
COPY submission.json /app/submission.json

# Expose HTTP port 8080 as specified in Page 3
EXPOSE 8080

# Healthcheck to verify the server is ready to accept submissions
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Launch compliant Uvicorn server on port 8080
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
