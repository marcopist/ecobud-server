FROM python:3.11-alpine

COPY . /app
WORKDIR /app

RUN pip install .

CMD source /app/startserver.sh