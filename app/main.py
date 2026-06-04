from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from .routers.users import router as users_router
from .routers.admin import router as admin_router
from .routers.comments import router as comments_router
from .routers.media import router as media_router
from .config import settings
from .exceptions import APIException


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ===================== GLOBAL EXCEPTION HANDLERS =====================

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # In production you might want to log this
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."}
    )


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