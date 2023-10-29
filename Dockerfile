# =========
FROM alpine:3.18 AS base

ENV PATH="/app/.venv/bin:$PATH" \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1
RUN apk add --no-cache git python3

# =========
FROM base AS dev

WORKDIR /app
RUN apk add --no-cache gcc linux-headers musl-dev make poetry python3-dev
COPY pyproject.toml poetry.lock poetry.toml ./

# =========
FROM dev AS deps

RUN poetry install --only main

# =========
FROM deps AS test

RUN poetry install --with test
COPY . .
RUN pip install .
RUN make checks

# =========
FROM deps AS docs

RUN poetry install --with docs
COPY docs ./docs
COPY CONTRIBUTING.md mkdocs.yml ./
RUN mkdocs build

# =========
FROM scratch AS docs-site

COPY --from=docs /app/site /site

# =========
FROM deps AS install

COPY . .
RUN poetry build
RUN pip install dist/gitopscli-*.whl

# =========
FROM base as final

COPY --from=install /app/.venv /app/.venv
ENTRYPOINT ["gitopscli"]
