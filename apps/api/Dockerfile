FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (gcc for native extensions)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright Chromium browser + OS deps for headless JS rendering
RUN playwright install --with-deps chromium

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Start server
# Render sets $PORT dynamically; default to 8000 for local dev
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
