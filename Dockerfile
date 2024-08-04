FROM python:3.10-slim

RUN pip install poetry

WORKDIR /app

COPY . .

RUN poetry config virtualenvs.create false && poetry install --no-dev

ENTRYPOINT ["hbd"]
