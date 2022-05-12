# =========
FROM python:3.8-alpine AS base

ENV PATH="/opt/venv/bin:$PATH"
RUN apk add --no-cache git

# =========
FROM base AS dev

WORKDIR /workdir
RUN apk add --no-cache gcc linux-headers musl-dev make
RUN python -m venv /opt/venv
RUN pip install --upgrade pip

# =========
FROM dev AS deps

COPY setup.py .
RUN pip install .

# =========
FROM deps AS test

COPY requirements-test.txt .
RUN pip install -r requirements-test.txt
COPY . .
RUN pip install .
RUN make checks

# =========
FROM dev AS docs

COPY requirements-docs.txt .
RUN pip install -r requirements-docs.txt
COPY docs ./docs
COPY CONTRIBUTING.md mkdocs.yml ./
RUN mkdocs build

# =========
FROM scratch AS docs-site

COPY --from=docs /workdir/site /site

# =========
FROM deps AS install

COPY . .
RUN pip install .

# =========
FROM base as final

COPY --from=install /opt/venv /opt/venv
ENTRYPOINT ["gitopscli"]
