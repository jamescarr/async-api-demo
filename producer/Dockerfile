FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY app ./app

# Sync dependencies and install the package (makes entry points available)
RUN uv sync --no-dev && uv pip install -e .

# Run the producer
CMD ["uv", "run", "producer", "run"]
