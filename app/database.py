from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from .config import settings

# Important: statement_cache_size=0 fixes PgBouncer + asyncpg issues
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,                    # Helps with stale connections
    connect_args={"statement_cache_size": 0}
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass
 

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session