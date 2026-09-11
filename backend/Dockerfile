FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for DuckDB, etc. if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directory just in case
RUN mkdir -p /app/data

# Expose port (overridden in docker-compose)
EXPOSE 8000
