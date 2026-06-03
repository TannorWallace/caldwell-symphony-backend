from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from .routers.users import router as users_router
from .routers.admin import router as admin_router
from .routers.comments import router as comments_router
from .routers.media import router as media_router
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("✅ Application started")
    yield
    print("🛑 Application shutting down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# ===================== SECURITY MIDDLEWARE =====================

# CORS - Now safely using the list from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Trusted Host (only enabled in production)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# Basic security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ===================== ROUTERS =====================

app.include_router(users_router)
app.include_router(admin_router)
app.include_router(comments_router)
app.include_router(media_router)


@app.get("/")
async def root():
    return {
        "message": "Caldwell Symphony API is running",
        "docs_enabled": settings.DEBUG
    } 