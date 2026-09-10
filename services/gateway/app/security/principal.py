"""Личность вызывающего и заголовки, которыми она едет дальше.

Имя кодируется процентами: заголовок HTTP допускает только ASCII, а имя
пользователя вполне может оказаться кириллицей.
"""

from dataclasses import dataclass
from urllib.parse import quote

HEADER_SUBJECT = "x-user-id"
HEADER_USERNAME = "x-user-name"
HEADER_ROLES = "x-user-roles"

HEADERS = frozenset({HEADER_SUBJECT, HEADER_USERNAME, HEADER_ROLES})


@dataclass(frozen=True, slots=True)
class Principal:
    subject: str
    username: str
    roles: frozenset[str]

    def has_any(self, required: frozenset[str]) -> bool:
        return bool(self.roles & required)

    def headers(self) -> dict[str, str]:
        return {
            HEADER_SUBJECT: self.subject,
            HEADER_USERNAME: quote(self.username),
            HEADER_ROLES: ",".join(sorted(self.roles)),
        }
