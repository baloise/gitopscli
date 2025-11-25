# =========
FROM alpine:3.22 AS base

ENV PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
RUN apk add --no-cache git python3

# =========
FROM base AS dev

WORKDIR /app
RUN apk add --no-cache gcc linux-headers musl-dev make python3-dev

# =========
FROM dev AS deps

RUN --mount=from=ghcr.io/astral-sh/uv:0.8,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.git/,target=.git/,ro \
    uv sync --locked --no-install-project --no-editable

# =========
FROM deps AS test

COPY . .
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --group=test
RUN make checks

# =========
FROM deps AS docs

RUN --mount=from=ghcr.io/astral-sh/uv:0.8,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.git/,target=.git/,ro \
    uv sync --locked --no-install-project --group=docs
COPY docs ./docs
COPY CONTRIBUTING.md mkdocs.yml ./
RUN mkdocs build

# =========
FROM scratch AS docs-site

COPY --from=docs /app/site /site

# =========
FROM deps AS install

COPY . .
RUN --mount=from=ghcr.io/astral-sh/uv:0.8,source=/uv,target=/bin/uv \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.git/,target=.git/,ro \
    uv sync --locked --no-editable

# =========
FROM base AS final

COPY --from=install /app/.venv /app/.venv
ENV AZURE_DEVOPS_CACHE_DIR="/tmp/.azure-devops"
ENTRYPOINT ["gitopscli"]
