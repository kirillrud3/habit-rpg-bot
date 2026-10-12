"""Подключение к БД. Единственный модуль, знающий про aiosqlite.

Для перехода на PostgreSQL достаточно реализовать этот же интерфейс
(connect / close / init_schema / execute / executemany / fetchone / fetchall /
transaction) поверх asyncpg и заменить плейсхолдеры `?` на `$1, $2...`.
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Sequence
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn: aiosqlite.Connection | None = None
        self._lock = asyncio.Lock()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("База данных не подключена")
        return self._conn

    async def connect(self) -> None:
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA foreign_keys = ON")
        await self._conn.execute("PRAGMA journal_mode = WAL")
        await self._conn.commit()

    async def init_schema(self) -> None:
        await self.conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        await self.conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """Атомарный блок: коммит при успехе, откат при исключении.

        Запись идёт через одно соединение, поэтому транзакции сериализуются локом.
        """
        async with self._lock:
            try:
                yield
                await self.conn.commit()
            except BaseException:
                await self.conn.rollback()
                raise

    # Методы ниже не коммитят — используй их внутри transaction().
    async def execute(self, sql: str, params: Sequence[Any] = ()) -> int:
        cursor = await self.conn.execute(sql, params)
        rowcount = cursor.rowcount
        await cursor.close()
        return rowcount

    async def executemany(self, sql: str, params: Iterable[Sequence[Any]]) -> None:
        await self.conn.executemany(sql, params)

    async def fetchone(self, sql: str, params: Sequence[Any] = ()) -> aiosqlite.Row | None:
        async with self.conn.execute(sql, params) as cursor:
            return await cursor.fetchone()

    async def fetchall(self, sql: str, params: Sequence[Any] = ()) -> list[aiosqlite.Row]:
        async with self.conn.execute(sql, params) as cursor:
            return list(await cursor.fetchall())
