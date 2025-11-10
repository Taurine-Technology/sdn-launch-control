# Multi-stage build for optimized image size
# Stage 1: Builder - Install dependencies and build Python packages
FROM python:3.10-slim AS builder

# Ensure that output is sent straight to terminal (without buffering)
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/app/

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-dev \
        gcc \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements.txt ./
COPY requirements.yml ./

# Install Python dependencies with BuildKit cache mount for faster rebuilds
# Note: --mount=type=cache requires BuildKit (DOCKER_BUILDKIT=1)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Stage 2: Runtime - Minimal production image
FROM python:3.10-slim AS runtime

# Ensure that output is sent straight to terminal (without buffering)
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/app/

# Install only runtime system dependencies (no build tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ansible \
        ssh \
        sshpass \
        libpq-dev \
        fping \
    && rm -rf /var/lib/apt/lists/*

# Install Ansible collections (runtime requirement)
COPY requirements.yml ./
RUN ansible-galaxy collection install -r requirements.yml

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code last (for better layer caching)
# Code changes won't invalidate dependency layers
COPY . .
