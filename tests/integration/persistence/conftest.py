from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from documentor.infrastructure.database import Base
from documentor.infrastructure.persistence import orm_models  # noqa: F401


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("pgvector/pgvector:pg16") as container:
        yield container


@pytest.fixture(scope="session")
def database_url(postgres_container: PostgresContainer) -> str:
    url = postgres_container.get_connection_url()
    return url.replace("psycopg2", "asyncpg")


@pytest_asyncio.fixture
async def session_factory(
    database_url: str,
) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    engine = create_async_engine(database_url)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
