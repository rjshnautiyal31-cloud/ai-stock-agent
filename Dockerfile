# =================-------------------------------------------------------------
# Stage 1: Build stage to compile dependencies and slim size
# =================-------------------------------------------------------------
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =================-------------------------------------------------------------
# Stage 2: Minimalist runtime execution stage
# =================-------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Copy the pre-compiled packages from the builder stage
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy your python source code
COPY src/ /app/src/

# Expose port 8080 (Cloud Run standard port)
EXPOSE 8080

# Default entrypoint (can be overridden by Cloud Run command/args)
ENTRYPOINT ["uvicorn"]
