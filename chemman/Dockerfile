FROM python:3.13.5-slim-bookworm AS poetry
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN pip install -U pip
RUN pip install poetry
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -f requirements.txt --output requirements.txt

FROM python:3.13.5-slim-bookworm
RUN apt-get update && apt-get install -y netcat
RUN addgroup --system app && adduser --system --group app --home /app
WORKDIR /app
COPY --from=poetry /app/requirements.txt .
RUN pip install -U pip
RUN pip install -r requirements.txt
COPY . .
RUN mkdir -p /app/{cp_static,uploads}
RUN chown -R app:app /app
RUN chmod +x /app/entrypoint.sh
USER app
ENTRYPOINT [ "/app/entrypoint.sh" ]
