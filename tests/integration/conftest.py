from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.postgres import PostgresContainer

from documentor.infrastructure.database import Base
from documentor.infrastructure.persistence import orm_models  # noqa: F401

_CREATE_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION chunks_search_vector_update() RETURNS trigger AS $$
BEGIN
  NEW.search_vector := to_tsvector(NEW.language::regconfig, NEW.text);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""

_CREATE_TRIGGER_SQL = """
CREATE OR REPLACE TRIGGER trg_chunks_search_vector
BEFORE INSERT OR UPDATE OF text, language ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_search_vector_update();
"""


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
        # Install the trigger that maintains search_vector per chunk language.
        # In production this is done by migration 005. In tests, create_all only
        # creates the ORM table structure so we need to install the trigger manually.
        await conn.execute(text(_CREATE_TRIGGER_FUNCTION_SQL))
        await conn.execute(text(_CREATE_TRIGGER_SQL))

    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
