"""Каркас потребителя RabbitMQ.

Очередь и биндинги объявлены декларативно в deploy/rabbitmq/definitions.json —
потребитель их не создаёт, только подписывается.
"""

import asyncio
import logging
from collections.abc import Awaitable, Callable

import aio_pika
from google.protobuf.json_format import Parse, ParseError
from mirea.events.v1 import events_pb2

from app.infra import tracing

log = logging.getLogger(__name__)

Handler = Callable[[events_pb2.EventEnvelope], Awaitable[None]]

# Без ограничения брокер вывалит в потребителя всю очередь разом, и при
# падении процесса вся пачка вернётся необработанной.
PREFETCH = 16


class Consumer:
    def __init__(self, amqp_url: str, queue: str) -> None:
        self._url = amqp_url
        self._queue_name = queue
        self._routes: dict[str, Handler] = {}
        self._fallback: Handler | None = None
        self._connection: aio_pika.abc.AbstractRobustConnection | None = None
        self._task: asyncio.Task | None = None

    def handle(self, routing_key: str, handler: Handler) -> None:
        self._routes[routing_key] = handler

    def handle_all(self, handler: Handler) -> None:
        """Один обработчик на весь поток — для подписчиков с биндингом `#`."""
        self._fallback = handler

    async def start(self) -> None:
        self._connection = await aio_pika.connect_robust(self._url)
        channel = await self._connection.channel()
        await channel.set_qos(prefetch_count=PREFETCH)

        queue = await channel.get_queue(self._queue_name)
        self._task = asyncio.create_task(queue.consume(self._on_message, no_ack=False))
        log.info("слушаем очередь %s", self._queue_name)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
        if self._connection is not None:
            await self._connection.close()

    async def _on_message(self, message: aio_pika.abc.AbstractIncomingMessage) -> None:
        try:
            envelope = Parse(message.body.decode(), events_pb2.EventEnvelope())
        except (ParseError, UnicodeDecodeError):
            log.exception("не разобрали событие, message_id=%s", message.message_id)
            await message.reject(requeue=False)
            return

        # Трасса продолжается: контекст пришёл вместе с событием.
        tracing.set_current(tracing.parse(envelope.traceparent))

        handler = self._routes.get(envelope.routing_key, self._fallback)
        if handler is None:
            # На ключ никто не подписан — подтверждаем, иначе очередь встанет.
            log.warning("обработчик не найден: %s", envelope.routing_key)
            await message.ack()
            return

        try:
            await handler(envelope)
        except Exception:
            log.exception(
                "обработка не удалась: %s, event_id=%s, trace_id=%s",
                envelope.routing_key, envelope.event_id, tracing.trace_id(),
            )
            # Повторять бессмысленно или опасно — в dead-letter.
            await message.reject(requeue=False)
            return

        await message.ack()
