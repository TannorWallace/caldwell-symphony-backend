# Use a slim Python image
# Why: Smaller than the full image; still has everything Python needs
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies that some Python packages need
# Why: psycopg / asyncpg sometimes need libpq; keep it minimal
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
# Why: Same caching idea as the frontend — requirements rarely change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# FastAPI/Uvicorn default port
EXPOSE 8000

# Run with Uvicorn
# Why: Production-ready ASGI server; --host 0.0.0.0 makes it reachable inside the container network
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]