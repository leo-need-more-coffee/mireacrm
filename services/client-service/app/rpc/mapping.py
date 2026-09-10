"""Перевод доменных моделей в сообщения protobuf."""

from mirea.client.v1 import client_pb2

from app import models

CHANNEL_TO_PROTO = {
    models.PreferredChannel.SMS: client_pb2.PREFERRED_CHANNEL_SMS,
    models.PreferredChannel.EMAIL: client_pb2.PREFERRED_CHANNEL_EMAIL,
    models.PreferredChannel.TELEGRAM: client_pb2.PREFERRED_CHANNEL_TELEGRAM,
}


def contacts(client: models.Client) -> client_pb2.ClientContacts:
    return client_pb2.ClientContacts(
        client_id=str(client.id),
        full_name=client.full_name,
        phone=client.phone,
        email=client.email,
        telegram=client.telegram,
        preferred=CHANNEL_TO_PROTO[client.preferred],
    )
