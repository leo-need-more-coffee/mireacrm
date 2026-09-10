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

COPY services/core-service/pyproject.toml services/core-service/alembic.ini /srv/
COPY services/core-service/app /srv/app
COPY services/core-service/migrations /srv/migrations
RUN pip install .

COPY services/core-service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 1001 core && chown -R core /srv
USER core

EXPOSE 8001 9001
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
