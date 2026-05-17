FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir .

# Copy source
COPY sibyl/ sibyl/
COPY scripts/ scripts/
COPY public/ public/


# Port
ENV PORT=8001
EXPOSE ${PORT}

# Run
CMD uvicorn sibyl.server:app --host 0.0.0.0 --port ${PORT:-8001} --log-level info
