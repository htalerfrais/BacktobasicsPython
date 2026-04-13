FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-root --no-interaction

COPY project/ ./project/

# pour pouvoir importer des modules src.xxx ...
ENV PYTHONPATH=/app/project