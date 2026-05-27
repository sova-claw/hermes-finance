FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml .
COPY finance_api/ finance_api/
RUN uv pip install --system --no-cache .

FROM python:3.12-slim AS runtime
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
RUN chmod +x entrypoint.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
