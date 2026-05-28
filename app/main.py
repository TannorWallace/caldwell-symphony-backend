from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .dependencies import get_current_active_user, get_current_admin_user
from .routers.users import router as users_router
from .routers.admin import router as admin_router
from .routers.comments import router as comments_router
from .routers.media import router as media_router
from .database import engine
from .models.models import Base

# Lifespan event to create tables on startup (perfect for prototyping)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")
    yield

app = FastAPI(
    title="Caldwell Symphony API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(admin_router)
app.include_router(comments_router)
app.include_router(media_router)

@app.get("/")
async def root():
    return {"message": "🚀 Caldwell Symphony Backend is running cleanly!"}