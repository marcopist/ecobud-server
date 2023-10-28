FROM python:3.11-alpine

COPY . /app
WORKDIR /app

RUN pip install .

ENTRYPOINT ["python", "-m", "app"]