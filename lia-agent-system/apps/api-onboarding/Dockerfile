FROM python:3.11-slim

WORKDIR /workspace

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy workspace pyproject (UV workspace resolution)
COPY pyproject.toml uv.lock* ./

# Install workspace libs (ordered by dependency)
COPY libs/ libs/
RUN uv pip install --system \
    -e libs/config \
    -e libs/utils \
    -e libs/audit \
    -e libs/messaging \
    -e libs/models \
    -e libs/schemas \
    -e libs/services \
    -e libs/events

# Install api-onboarding deps
COPY apps/api-onboarding/pyproject.toml apps/api-onboarding/pyproject.toml
RUN uv pip install --system -e apps/api-onboarding

# Copy application code
COPY app/ app/
COPY apps/api-onboarding/ apps/api-onboarding/

ENV PYTHONPATH=/workspace

EXPOSE 8003

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8003", \
     "--app-dir", "apps/api-onboarding", \
     "--workers", "2"]
