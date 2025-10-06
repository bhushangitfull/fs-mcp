# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml .

RUN uv sync --frozen




COPY src/ .




ENV PYTHONUNBUFFERED=1
ENV PORT=${PORT:-8000}

# Health check to ensure the server is running
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; import os; urllib.request.urlopen(f'http://localhost:{os.getenv(\"PORT\", 8000)}/health')"

# Run the MCP server
CMD ["uv", "run", "python", "main.py"]
