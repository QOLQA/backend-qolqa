FROM python:3.12-slim AS base
WORKDIR /code
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN pip install pipenv

FROM base AS builder
ENV PIPENV_VENV_IN_PROJECT=1
RUN apt-get install -y build-essential

FROM builder AS installer
COPY Pipfile Pipfile.lock ./
RUN pipenv install

FROM base AS runner
COPY --from=installer /code/.venv /code/.venv
COPY . /code
CMD pipenv run uvicorn main:app --reload
