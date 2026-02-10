from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Migrations for existing DBs
    async with async_session() as session:
        migrations = [
            "ALTER TABLE tasks ADD COLUMN sprint_id INTEGER REFERENCES sprints(id)",
            "ALTER TABLE jira_connections ADD COLUMN jira_board_id INTEGER",
            "ALTER TABLE projects ADD COLUMN join_code VARCHAR(20)",
            "CREATE UNIQUE INDEX IF NOT EXISTS ix_projects_join_code ON projects(join_code)",
        ]
        for sql in migrations:
            try:
                await session.execute(text(sql))
                await session.commit()
            except Exception:
                await session.rollback()
