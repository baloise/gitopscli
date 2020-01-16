FROM python:3.7-slim-buster

WORKDIR /opt/gitopscli

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN pip install .

ENTRYPOINT ["gitopscli"]