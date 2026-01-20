"""URL configuration for shared app."""
from __future__ import annotations

from django.http import JsonResponse
from django.urls import path

app_name = "shared"


def health_check(request) -> JsonResponse:  # noqa: ANN001, ARG001
    """Health check endpoint.

    Returns:
        JSON response with service status.
    """
    from django.db import connection

    health = {
        "status": "healthy",
        "services": {},
    }

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health["services"]["database"] = "healthy"
    except Exception as e:
        health["services"]["database"] = f"unhealthy: {e}"
        health["status"] = "degraded"

    # Check Redis connection (if available)
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", timeout=1)
        if cache.get("health_check") == "ok":
            health["services"]["cache"] = "healthy"
        else:
            health["services"]["cache"] = "unhealthy: cache read failed"
            health["status"] = "degraded"
    except Exception as e:
        health["services"]["cache"] = f"unhealthy: {e}"
        health["status"] = "degraded"

    status_code = 200 if health["status"] == "healthy" else 503
    return JsonResponse(health, status=status_code)


def readiness_check(request) -> JsonResponse:  # noqa: ANN001, ARG001
    """Readiness check endpoint.

    Checks if the service is ready to receive traffic.

    Returns:
        JSON response indicating readiness.
    """
    return JsonResponse({"ready": True})


def liveness_check(request) -> JsonResponse:  # noqa: ANN001, ARG001
    """Liveness check endpoint.

    Simple check to verify the service is running.

    Returns:
        JSON response indicating the service is alive.
    """
    return JsonResponse({"alive": True})


urlpatterns = [
    path("health/", health_check, name="health"),
    path("ready/", readiness_check, name="ready"),
    path("live/", liveness_check, name="live"),
]
