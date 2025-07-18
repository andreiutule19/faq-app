from celery import Celery
from app.core.settings import settings

celery_app = Celery(
    "semantic_faq_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.services.embeddings_service","app.services.openai_service", "app.services.similarity_service"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60, 
    task_soft_time_limit=25 * 60, 
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)