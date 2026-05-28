FROM python:3.12-slim AS base

# set env variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# install uv, copies binary from official docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# set work directory
WORKDIR /app

# install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# copy application code
COPY app/ app/
COPY alembic.ini alembic.ini
COPY entrypoint.sh entrypoint.sh                                                                                                               

# security: non-root user
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

USER appuser

# place uv virtual environment on the path
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["sh", "entrypoint.sh"]