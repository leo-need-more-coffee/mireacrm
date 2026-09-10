"""Проверка принадлежности объекта вызывающему.

Роль проверяет шлюз, принадлежность — сервис-владелец: только он знает, чей
это объект. Правило одно на систему: администратор и управляющий работают
с чужими объектами, специалист — только со своими.
"""

import uuid

from app.infra.errors import ForbiddenError
from app.infra.identity import Caller, current


def ensure_owner(owner_id: uuid.UUID | str | None, what: str, caller: Caller | None = None) -> None:
    """Пропускает вызов, если объект принадлежит вызывающему.

    Вызов без личности — обращение изнутри системы, а не от человека:
    потребитель события или служебная задача. Ограничивать их нечем и незачем,
    снаружи такой вызов не сделать — заголовки личности шлюз затирает.
    """
    caller = current() if caller is None else caller
    if not caller.known or caller.privileged:
        return

    # Пустая привязка означает, что учётной записи не соответствует ни один
    # сотрудник. Отказ по умолчанию: иначе такая учётка видела бы всё.
    if not caller.employee_id or str(owner_id) != caller.employee_id:
        raise ForbiddenError(what)
