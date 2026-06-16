FROM python:3.11-slim

WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from monorepo root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install internal libs (order: config first, then dependents)
COPY libs/config libs/config
COPY libs/utils libs/utils
COPY libs/audit libs/audit
COPY libs/messaging libs/messaging
COPY libs/models libs/models
COPY libs/agents-core libs/agents-core
COPY libs/services libs/services
COPY libs/contexts libs/contexts
COPY libs/auth libs/auth
RUN pip install --no-cache-dir \
    -e libs/config \
    -e libs/utils \
    -e libs/audit \
    -e libs/messaging \
    -e libs/models \
    -e libs/agents-core \
    -e libs/services \
    -e libs/contexts \
    -e libs/auth

# Copy application code
COPY app/ app/
COPY apps/ apps/

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--app-dir", "apps/api-agentes"]
