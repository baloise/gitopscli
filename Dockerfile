FROM python:3.7-alpine AS base-image

ENV PATH="/opt/venv/bin:$PATH"
RUN apk add --no-cache git

FROM base-image AS deps-image

RUN apk add --no-cache gcc linux-headers musl-dev \
 && python -m venv /opt/venv \
 && pip install --upgrade pip
WORKDIR /workdir
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM deps-image AS test-image

COPY requirements-dev.txt .
RUN pip install -r requirements-dev.txt
COPY . .
RUN black --check -l 120 -t py37 gitopscli tests setup.py
RUN pylint gitopscli
RUN python -m pytest -v

FROM deps-image AS build-image

COPY . .
RUN pip install .

FROM base-image AS runtime-image

COPY --from=build-image /opt/venv /opt/venv
ENTRYPOINT ["gitopscli"]