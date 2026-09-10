FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Контекст сборки — корень репозитория: сервису нужны из него контракты
# и общий обвяз. Оба ставятся до кода сервиса — меняются они реже,
# и слой с ними переиспользуется между сборками.
COPY gen/python /srv/contracts
RUN pip install /srv/contracts

COPY libs/py-common /srv/common
RUN pip install "/srv/common[db,events,grpc]"

COPY services/catalog-service/pyproject.toml services/catalog-service/alembic.ini /srv/
COPY services/catalog-service/app /srv/app
COPY services/catalog-service/migrations /srv/migrations
RUN pip install .

COPY services/catalog-service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 1002 catalog && chown -R catalog /srv
USER catalog

EXPOSE 8002 9002
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
