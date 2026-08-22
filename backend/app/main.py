import logging
import os
import time

from fastapi import FastAPI, HTTPException, status  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore

from app.api.auth import router as auth_router
from app.api.email import router as email_router
from app.api.oauth import router as oauth_router
from app.api.user_session import router as user_session_router
from app.core.celery_app import get_celery_health_status
from app.core.jwt import cleanup_expired_tokens, get_redis_health_status
from app.core.storage import get_storage_health_status
from app.db.session import get_database_status, test_database_connection
from app.middleware.audit import AuditMiddleware
from app.middleware.auto_refresh import AutoRefreshMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, get_rate_limit_status
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Secure Authentication API",
    description="Enhanced authentication backend with comprehensive security features",
    version="2.0.0",
    docs_url="/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.environ.get("ENVIRONMENT") != "production" else None,
)

# CORS configuration - must be first middleware
allowed_origins_env = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
allow_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

# Add CORS middleware first (before all other middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Request-ID"],
)

# Request context first so downstream middlewares/handlers can use request_id
app.add_middleware(RequestContextMiddleware)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(RateLimitMiddleware)

# Auto-refresh middleware for seamless token management
app.add_middleware(AutoRefreshMiddleware)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(oauth_router, prefix="/api/v1")
app.include_router(email_router, prefix="/api/v1")
app.include_router(user_session_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Secure Authentication API",
        "version": "2.0.0",
        "docs": "/docs" if os.environ.get("ENVIRONMENT") != "production" else None,
        "health": "/health",
        "status": "/status",
    }


@app.get("/health")
async def health():
    """Enhanced health check with detailed system status."""
    health_status = {"status": "ok", "timestamp": time.time(), "version": "2.0.0", "services": {}}

    # Check database
    try:
        db_status = get_database_status()
        health_status["services"]["database"] = db_status
        if db_status.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["database"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis_status = get_redis_health_status()
        health_status["services"]["redis"] = redis_status
        if redis_status.get("status") != "connected":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["redis"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check rate limiting
    try:
        rate_limit_status = get_rate_limit_status()
        health_status["services"]["rate_limiting"] = rate_limit_status
    except Exception as e:
        health_status["services"]["rate_limiting"] = {"status": "error", "error": str(e)}

    # Check Celery
    try:
        celery_status = get_celery_health_status()
        health_status["services"]["celery"] = celery_status
        if celery_status.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["celery"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # Check Storage (MinIO)
    try:
        storage_status = get_storage_health_status()
        health_status["services"]["storage"] = storage_status
        if storage_status.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["storage"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    return health_status


@app.get("/status")
async def get_status():
    """Detailed system status for monitoring."""
    try:
        return {
            "timestamp": time.time(),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "database": get_database_status(),
            "redis": get_redis_health_status(),
            "celery": get_celery_health_status(),
            "storage": get_storage_health_status(),
            "rate_limiting": get_rate_limit_status(),
            "middleware": {
                "security_headers": "enabled",
                "audit_logging": "enabled",
                "rate_limiting": "enabled",
                "auto_refresh": "enabled",
                "cors": "enabled",
            },
        }
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Status check failed"
        )


@app.post("/admin/cleanup")
async def admin_cleanup():
    """Admin endpoint to trigger cleanup operations."""
    try:
        # Clean up expired tokens
        cleanup_expired_tokens()

        return {
            "status": "success",
            "message": "Cleanup operations completed",
            "timestamp": time.time(),
        }
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Cleanup failed"
        )


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Test critical services
        db_healthy = test_database_connection()
        if not db_healthy:
            logger.error("Database connection failed during startup")

        # Perform initial cleanup
        cleanup_expired_tokens()

        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    try:
        # Perform final cleanup
        cleanup_expired_tokens()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
