# Dockerfile for paperless-ngx-correspondent-manager
FROM python:3.13-slim

WORKDIR /app

# Install build dependencies
RUN pip install --upgrade pip

# Copy only requirements first for caching
COPY pyproject.toml ./
COPY README.md ./

# Install project dependencies
RUN pip install .

# Copy the rest of the code
COPY src/ ./src/

# Set entrypoint for CLI usage
ENTRYPOINT ["python", "-m", "paperless_ngx_correspondent_manager.cli"]

# Default command shows help
CMD ["--help"]
