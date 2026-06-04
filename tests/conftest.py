import pytest
import uuid
from dataclasses import dataclass
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db, Base
from app.models.models import User as UserModel, Media as MediaModel
from app.routers.users import get_password_hash
from app.dependencies import get_current_active_user


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)


@dataclass
class TestUserData:
    __test__ = False
    id: int
    email: str
    username: str
    is_active: bool = True
    is_admin: bool = False


@dataclass
class TestMediaData:
    __test__ = False
    id: int


@dataclass
class FakeUser:
    """Used for dependency override in tests."""
    __test__ = False
    id: int
    email: str = "test@example.com"
    username: str = "testuser"
    is_active: bool = True
    is_admin: bool = False


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ==================== REUSABLE AUTH FIXTURES ====================

@pytest.fixture
async def authenticated_client(client: AsyncClient, test_user: TestUserData):
    """Returns a client authenticated as a regular (non-admin) user."""
    def override():
        return FakeUser(
            id=test_user.id,
            email=test_user.email,
            username=test_user.username,
            is_active=True,
            is_admin=False
        )
    app.dependency_overrides[get_current_active_user] = override
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_client(client: AsyncClient, test_admin: TestUserData):
    """Returns a client authenticated as an admin user."""
    def override():
        return FakeUser(
            id=test_admin.id,
            email=test_admin.email,
            username=test_admin.username,
            is_active=True,
            is_admin=True
        )
    app.dependency_overrides[get_current_active_user] = override
    yield client
    app.dependency_overrides.clear()


# ==================== TEST DATA FIXTURES ====================

@pytest.fixture
async def test_user(db_session: AsyncSession) -> TestUserData:
    unique = uuid.uuid4().hex[:8]
    email = f"test_{unique}@example.com"
    username = f"testuser_{unique}"

    real_user = UserModel(
        email=email,
        username=username,
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(real_user)
    await db_session.commit()
    await db_session.refresh(real_user)

    return TestUserData(id=real_user.id, email=email, username=username)


@pytest.fixture
async def test_admin(db_session: AsyncSession) -> TestUserData:
    unique = uuid.uuid4().hex[:8]
    email = f"admin_{unique}@example.com"
    username = f"adminuser_{unique}"

    real_admin = UserModel(
        email=email,
        username=username,
        hashed_password=get_password_hash("adminpassword123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(real_admin)
    await db_session.commit()
    await db_session.refresh(real_admin)

    return TestUserData(id=real_admin.id, email=email, username=username, is_admin=True)


@pytest.fixture
async def test_media(db_session: AsyncSession, test_user: TestUserData) -> TestMediaData:
    real_media = MediaModel(
        media_type="image",
        bucket="media",
        file_path="test.jpg",
        public_url="https://example.com/test.jpg",
        title="Test Media",
        user_id=test_user.id,
    )
    db_session.add(real_media)
    await db_session.commit()
    await db_session.refresh(real_media)

    return TestMediaData(id=real_media.id)