"""Health check endpoints."""

from fastapi import APIRouter, status

from mindwell import __version__
from mindwell.config import get_settings
from mindwell.schemas import HealthCheck

router = APIRouter()
settings = get_settings()


@router.get(
    "/health",
    response_model=HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API and its dependencies",
)
async def health_check() -> HealthCheck:
    """
    Perform a health check on the API.
    
    Returns the status of:
    - API service
    - Database connection
    - LLM service availability
    """
    # TODO: Implement actual database and LLM connectivity checks
    database_connected = True  # Placeholder
    llm_available = settings.openai_api_key is not None or settings.use_azure_openai

    return HealthCheck(
        status="healthy",
        version=__version__,
        environment=settings.app_env,
        database_connected=database_connected,
        llm_available=llm_available,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Simple liveness probe for Kubernetes/container orchestration",
)
async def liveness():
    """Simple liveness check - returns 200 if the service is running."""
    return {"status": "alive"}


@router.get(
    "/health/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Readiness probe checking if the service is ready to accept traffic",
)
async def readiness():
    """
    Readiness check - verifies the service is ready to accept requests.
    
    Checks:
    - Configuration is loaded
    - Required services are available
    """
    # TODO: Add actual readiness checks (database pool, LLM client, etc.)
    ready = True
    
    if not ready:
        return {"status": "not_ready", "reason": "Dependencies not available"}
    
    return {"status": "ready"}
