FROM python:3.7-slim-buster

WORKDIR /opt/gitopscli

COPY . .

RUN pip install -r requirements.txt \
 && pip install .

ENTRYPOINT ["gitopscli"]