"""Публичные ключи Keycloak.

Ключи меняются при ротации, поэтому кэш обновляется по незнакомому kid.
Обновление ограничено по частоте: иначе поток запросов с выдуманным kid
превращается в поток запросов к Keycloak.
"""

import asyncio
import json
import logging
from time import monotonic

import httpx
from jwt.algorithms import RSAAlgorithm

log = logging.getLogger(__name__)


class KeyStore:
    def __init__(self, url: str, cooldown: float = 30.0, client: httpx.AsyncClient | None = None):
        self._url = url
        self._cooldown = cooldown
        self._client = client or httpx.AsyncClient(timeout=5.0)
        self._owns_client = client is None
        self._keys: dict[str, object] = {}
        self._fetched_at = float("-inf")
        self._lock = asyncio.Lock()

    @property
    def loaded(self) -> bool:
        return bool(self._keys)

    async def key(self, kid: str) -> object | None:
        key = self._keys.get(kid)
        if key is not None:
            return key
        await self.refresh()
        return self._keys.get(kid)

    async def refresh(self, force: bool = False) -> bool:
        async with self._lock:
            if not force and monotonic() - self._fetched_at < self._cooldown:
                return bool(self._keys)
            try:
                response = await self._client.get(self._url)
                response.raise_for_status()
                document = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                log.warning("не удалось получить JWKS: %s", exc)
                return False

            self._fetched_at = monotonic()
            self._keys = {
                jwk["kid"]: RSAAlgorithm.from_jwk(json.dumps(jwk))
                for jwk in document.get("keys", ())
                if jwk.get("kty") == "RSA" and jwk.get("use", "sig") == "sig"
            }
            log.info("ключи Keycloak обновлены: %s", ", ".join(self._keys) or "пусто")
            return bool(self._keys)

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
