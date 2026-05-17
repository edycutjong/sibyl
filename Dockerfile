FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy source
COPY sibyl/ sibyl/
COPY scripts/ scripts/


# Port
ENV PORT=8001
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import httpx; httpx.get('http://localhost:${PORT}/health').raise_for_status()"

# Run
CMD ["uvicorn", "sibyl.server:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info"]
