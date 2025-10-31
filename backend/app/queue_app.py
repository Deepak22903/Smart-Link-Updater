import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "smartlinkupdater",
    broker=REDIS_URL,
    backend=os.getenv("CELERY_RESULT_BACKEND", REDIS_URL),
)

# Celery config basics
celery_app.conf.update(
    task_routes={
        "tasks.update_post_task": {"queue": os.getenv("CELERY_QUEUE", "default")},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_time_limit=int(os.getenv("TASK_TIME_LIMIT", "600")),
    task_soft_time_limit=int(os.getenv("TASK_SOFT_TIME_LIMIT", "540")),
)
