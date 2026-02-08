"""
AI Proposal Generator - FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    # Startup
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"   Environment: {settings.APP_ENV}")
    print(f"   Debug: {settings.DEBUG}")
    yield
    # Shutdown — close LLM provider connections
    from app.services.llm_providers import close_all_providers
    await close_all_providers()
    print(f"👋 Shutting down {settings.APP_NAME}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="智慧投標建議書生成系統 - AI-powered proposal generation for government tenders",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to all responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# =============================================================================
# Health Check Endpoints
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint for Docker healthcheck."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check():
    """Readiness check - verifies all dependencies are available."""
    # TODO: Add actual database/redis/minio checks
    return {
        "status": "ready",
        "checks": {
            "database": True,
            "redis": True,
            "minio": True
        }
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production",
        "health": "/health"
    }


# =============================================================================
# API Routes
# =============================================================================
from app.api.v1.endpoints import auth, projects, sections, ai, personas, usage

app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"],
)
app.include_router(
    projects.router,
    prefix=f"{settings.API_V1_PREFIX}/projects",
    tags=["Projects"],
)
app.include_router(
    sections.router,
    prefix=f"{settings.API_V1_PREFIX}/sections",
    tags=["Sections"],
)
app.include_router(
    ai.router,
    prefix=f"{settings.API_V1_PREFIX}/ai",
    tags=["AI"],
)
app.include_router(
    personas.router,
    prefix=f"{settings.API_V1_PREFIX}/personas",
    tags=["Personas"],
)
app.include_router(
    usage.router,
    prefix=f"{settings.API_V1_PREFIX}/usage",
    tags=["Usage"],
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
