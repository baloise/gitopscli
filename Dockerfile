FROM python:3.7-slim-buster AS base

RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/gitopscli

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

FROM base AS quality-gate

RUN pip install black pylint
RUN black --check -l 120 -t py37 gitopscli tests
RUN pylint gitopscli
RUN pytest -v

FROM base AS final

RUN pip install .

ENTRYPOINT ["gitopscli"]