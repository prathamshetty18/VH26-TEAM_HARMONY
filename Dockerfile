FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and data
COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/

# Pre-index vector database
RUN python -m src.embed_store

EXPOSE 8000

ENV PORT=8000
CMD [" sh\, \-c\, \uvicorn src.api:app --host 0.0.0.0 --port \]
