FROM python:3.7-slim-buster AS base

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/* \
 && pip install --upgrade pip

WORKDIR /opt/gitopscli

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY gitopscli gitopscli

FROM base AS quality-gate

COPY . .
RUN pip install -r requirements-dev.txt

RUN black --check -l 120 -t py37 gitopscli tests
RUN pylint gitopscli
RUN python -m pytest -v

FROM base AS final

COPY setup.py .
RUN pip install .

ENTRYPOINT ["gitopscli"]