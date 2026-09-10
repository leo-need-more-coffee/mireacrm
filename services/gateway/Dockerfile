FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

# Контекст сборки — корень репозитория: шлюзу нужен общий обвяз.
# Берётся только ядро: базы, брокера и gRPC у шлюза нет.
COPY libs/py-common /srv/common
RUN pip install /srv/common

COPY services/gateway/pyproject.toml /srv/
COPY services/gateway/app /srv/app
RUN pip install .

RUN useradd --system --uid 1001 gateway && chown -R gateway /srv
USER gateway

EXPOSE 8000
CMD ["python", "-m", "app"]
