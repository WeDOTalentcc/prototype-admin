FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (includes libs/)
COPY . .

# Install internal libs (order: config first, then dependents)
RUN pip install --no-cache-dir \
    -e libs/config \
    -e libs/utils \
    -e libs/audit \
    -e libs/messaging \
    -e libs/models \
    -e libs/agents-core \
    -e libs/services

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
