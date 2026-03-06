FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY config/ config/

RUN pip install --no-cache-dir -e ".[all]"

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
