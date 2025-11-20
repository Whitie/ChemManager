FROM python:3.13-slim

RUN apt update -y \
    && apt upgrade -y \
    && apt install --no-install-recommends --yes \
    build-essential python3-dev python3-poetry \
    libldap2-dev libsasl2-dev slapd ldap-utils tox \
    lcov valgrind

RUN mkdir /app

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry install --no-root

COPY ./chemman/ /app/

EXPOSE 8800

RUN chmod +x /app/entrypoint.sh

VOLUME ["/app/uploads", "/app/chemman"]

CMD ["/app/entrypoint.sh"]
