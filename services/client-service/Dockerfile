FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Контекст сборки — корень репозитория: сервису нужен gen/python из него.
COPY gen/python /srv/contracts
RUN pip install /srv/contracts

COPY services/client-service/pyproject.toml services/client-service/alembic.ini /srv/
COPY services/client-service/app /srv/app
COPY services/client-service/migrations /srv/migrations
RUN pip install .

COPY services/client-service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 1003 client && chown -R client /srv
USER client

EXPOSE 8005 9005
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
