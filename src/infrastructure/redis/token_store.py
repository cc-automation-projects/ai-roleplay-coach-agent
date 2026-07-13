"""Token store implementations — Redis (production) + InMemory (dev/test)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import redis.asyncio as aioredis


class InMemoryTokenStore:
    """In-memory refresh token store (dev/test — lost on restart).

    Max-size bounded (default 10 000); oldest token evicted when full.
    """

    def __init__(self, maxsize: int = 10_000) -> None:
        self._tokens: dict[str, UUID] = {}
        self._maxsize = maxsize

    async def store(self, user_id: UUID, token: str, _expires_at: datetime) -> None:
        if len(self._tokens) >= self._maxsize:
            oldest = next(iter(self._tokens))
            self._tokens.pop(oldest)
        self._tokens[token] = user_id

    async def validate(self, token: str) -> UUID | None:
        return self._tokens.get(token)

    async def revoke(self, token: str) -> None:
        self._tokens.pop(token, None)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        self._tokens = {k: v for k, v in self._tokens.items() if v != user_id}


class RedisTokenStore:
    """Redis-backed refresh token store with TTL expiry.

    Uses two key patterns::

        refresh_token:<token>  →  user_id (string, TTL = remaining lifetime)
        user_tokens:<user_id>  →  set of tokens (for bulk revoke)
    """

    _PREFIX = "refresh_token:"
    _USER_PREFIX = "user_tokens:"

    def __init__(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def store(self, user_id: UUID, token: str, expires_at: datetime) -> None:
        ttl = int((expires_at - datetime.now(UTC)).total_seconds())
        if ttl <= 0:
            return  # already expired, nothing to store
        token_key = self._PREFIX + token
        user_key = self._USER_PREFIX + str(user_id)
        await self._redis.set(token_key, str(user_id), ex=ttl)
        await self._redis.sadd(user_key, token)
        await self._redis.expire(user_key, ttl)

    async def validate(self, token: str) -> UUID | None:
        val = await self._redis.get(self._PREFIX + token)
        return UUID(val) if val is not None else None

    async def revoke(self, token: str) -> None:
        token_key = self._PREFIX + token
        val = await self._redis.get(token_key)
        if val is not None:
            user_id = UUID(val)
            await self._redis.delete(token_key)
            await self._redis.srem(self._USER_PREFIX + str(user_id), token)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        user_key = self._USER_PREFIX + str(user_id)
        tokens = await self._redis.smembers(user_key)
        if tokens:
            keys = [self._PREFIX + t for t in tokens]
            await self._redis.delete(*keys)
            await self._redis.delete(user_key)
