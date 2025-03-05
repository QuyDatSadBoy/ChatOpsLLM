"""
Celery application factory.

Connects to RabbitMQ as the broker and Redis as the result backend,
matching the architecture shown in the ChatOpsLLM system diagram.

Author: Trần Quý Đạt <tranquydat.work@gmail.com>
"""

import os

from celery import Celery

RABBITMQ_URL = os.getenv(
    "RABBITMQ_URL",
    "amqp://guest:guest@localhost:5672//",
)
REDIS_RESULT_URL = os.getenv(
    "REDIS_RESULT_URL",
    "redis://localhost:6379/2",
)

celery_app = Celery(
    "chatopsllm",
    broker=RABBITMQ_URL,
    backend=REDIS_RESULT_URL,
    include=["chatopsllm_api.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
