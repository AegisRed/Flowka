from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class Database:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine | None = None
        if database_url:
            self._engine = create_async_engine(database_url, pool_pre_ping=True)

    @property
    def engine(self) -> AsyncEngine | None:
        return self._engine

    async def ping(self) -> bool:
        if self._engine is None:
            return True
        try:
            async with self._engine.begin() as connection:
                await connection.execute(text("select 1"))
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
