"""Celery app (Redis broker/backend)."""
from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ocr",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)
celery_app.conf.update(
    task_track_started=True,
    worker_prefetch_multiplier=1,        # fair dispatch for long OCR tasks
    task_acks_late=True,
    # OOM-killed task gets requeued instead of stuck forever in "processing"
    task_reject_on_worker_lost=True,
    # Recycle each worker child after N tasks — PaddleOCR/OpenCV leak memory
    worker_max_tasks_per_child=20,
    # Hard/soft time limits so a hung/crashed task fails instead of hanging the job
    task_time_limit=600,                 # hard kill at 10 min
    task_soft_time_limit=540,            # raise SoftTimeLimitExceeded at 9 min
)
