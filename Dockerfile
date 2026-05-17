FROM python:3.12-slim

WORKDIR /app

# Copy source first for hatchling wheel build
COPY pyproject.toml README.md ./
COPY sibyl/ sibyl/

# Install dependencies and project
RUN pip install --no-cache-dir .

# Copy remaining assets
COPY scripts/ scripts/
COPY public/ public/

# Port
ENV PORT=8001
EXPOSE ${PORT}

# Run
CMD uvicorn sibyl.server:app --host 0.0.0.0 --port ${PORT:-8001} --log-level info
