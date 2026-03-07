"""
Health check tasks for monitoring system status
"""

import logging
import time
from typing import Any, Dict

from app.core import get_redis_health_status
from app.core.celery_app import celery_app
from app.db.session import get_db_health_status

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="app.tasks.health_check.check_system_health")
def check_system_health(self) -> Dict[str, Any]:
    """
    Check overall system health including database, Redis, and external services

    Returns:
        Dict: Health status information
    """
    start_time = time.time()

    try:
        health_status = {
            "timestamp": time.time(),
            "overall_status": "healthy",
            "checks": {},
            "duration_ms": 0,
        }

        # Check database health
        try:
            db_health = get_db_health_status()
            health_status["checks"]["database"] = db_health
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # Check Redis health
        try:
            redis_health = get_redis_health_status()
            health_status["checks"]["redis"] = redis_health
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            health_status["checks"]["redis"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # Check Celery worker health
        try:
            celery_health = self.app.control.inspect().stats()
            if celery_health:
                health_status["checks"]["celery"] = {
                    "status": "healthy",
                    "workers": len(celery_health),
                    "stats": celery_health,
                }
            else:
                health_status["checks"]["celery"] = {
                    "status": "unhealthy",
                    "error": "No workers available",
                }
                health_status["overall_status"] = "degraded"
        except Exception as e:
            logger.error(f"Celery health check failed: {e}")
            health_status["checks"]["celery"] = {"status": "unhealthy", "error": str(e)}
            health_status["overall_status"] = "degraded"

        # Calculate duration
        health_status["duration_ms"] = round((time.time() - start_time) * 1000, 2)

        logger.info(f"System health check completed in {health_status['duration_ms']}ms")
        return health_status

    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "timestamp": time.time(),
            "overall_status": "unhealthy",
            "error": str(e),
            "duration_ms": round((time.time() - start_time) * 1000, 2),
        }


@celery_app.task(bind=True, name="app.tasks.health_check.check_worker_health")
def check_worker_health(self) -> Dict[str, Any]:
    """
    Check individual worker health and performance

    Returns:
        Dict: Worker health information
    """
    try:
        worker_stats = self.app.control.inspect().stats()
        active_tasks = self.app.control.inspect().active()
        scheduled_tasks = self.app.control.inspect().scheduled()

        worker_health = {
            "timestamp": time.time(),
            "workers": {},
            "total_workers": len(worker_stats) if worker_stats else 0,
        }

        if worker_stats:
            for worker_name, stats in worker_stats.items():
                worker_health["workers"][worker_name] = {
                    "status": "healthy",
                    "stats": stats,
                    "active_tasks": len(active_tasks.get(worker_name, [])),
                    "scheduled_tasks": len(scheduled_tasks.get(worker_name, [])),
                }

        return worker_health

    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return {
            "timestamp": time.time(),
            "error": str(e),
            "total_workers": 0,
        }


@celery_app.task(bind=True, name="app.tasks.health_check.check_queue_health")
def check_queue_health(self) -> Dict[str, Any]:
    """
    Check queue health and backlog

    Returns:
        Dict: Queue health information
    """
    try:
        active_tasks = self.app.control.inspect().active()
        scheduled_tasks = self.app.control.inspect().scheduled()

        queue_health = {
            "timestamp": time.time(),
            "queues": {
                "email_sync": {"active": 0, "scheduled": 0},
                "oauth_cleanup": {"active": 0, "scheduled": 0},
                "health_check": {"active": 0, "scheduled": 0},
            },
            "total_active": 0,
            "total_scheduled": 0,
        }

        # Count tasks by queue
        if active_tasks:
            for worker_name, tasks in active_tasks.items():
                for task in tasks:
                    task_name = task.get("name", "")
                    if "email_sync" in task_name:
                        queue_health["queues"]["email_sync"]["active"] += 1
                    elif "oauth_cleanup" in task_name:
                        queue_health["queues"]["oauth_cleanup"]["active"] += 1
                    elif "health_check" in task_name:
                        queue_health["queues"]["health_check"]["active"] += 1
                    queue_health["total_active"] += 1

        if scheduled_tasks:
            for worker_name, tasks in scheduled_tasks.items():
                for task in tasks:
                    task_name = task.get("name", "")
                    if "email_sync" in task_name:
                        queue_health["queues"]["email_sync"]["scheduled"] += 1
                    elif "oauth_cleanup" in task_name:
                        queue_health["queues"]["oauth_cleanup"]["scheduled"] += 1
                    elif "health_check" in task_name:
                        queue_health["queues"]["health_check"]["scheduled"] += 1
                    queue_health["total_scheduled"] += 1

        return queue_health

    except Exception as e:
        logger.error(f"Queue health check failed: {e}")
        return {
            "timestamp": time.time(),
            "error": str(e),
            "total_active": 0,
            "total_scheduled": 0,
        }
