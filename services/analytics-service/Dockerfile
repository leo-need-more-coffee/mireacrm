FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Контекст сборки — корень репозитория: сервису нужен gen/python из него.
COPY gen/python /srv/contracts
RUN pip install /srv/contracts

COPY services/analytics-service/pyproject.toml services/analytics-service/alembic.ini /srv/
COPY services/analytics-service/app /srv/app
COPY services/analytics-service/migrations /srv/migrations
RUN pip install .

COPY services/analytics-service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 1005 analytics && chown -R analytics /srv
USER analytics

EXPOSE 8008
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
