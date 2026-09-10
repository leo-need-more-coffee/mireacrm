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

COPY services/billing-service/pyproject.toml services/billing-service/alembic.ini /srv/
COPY services/billing-service/app /srv/app
COPY services/billing-service/migrations /srv/migrations
RUN pip install .

COPY services/billing-service/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && useradd --system --uid 1004 billing && chown -R billing /srv
USER billing

EXPOSE 8006
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "-m", "app"]
