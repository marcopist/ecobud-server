FROM python:3.11-alpine

COPY . /app
WORKDIR /app

RUN pip install .

CMD gunicorn --workers=2 src.ecobud.app:app