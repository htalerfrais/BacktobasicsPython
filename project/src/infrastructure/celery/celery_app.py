import os
from celery import Celery

broker = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

app = Celery("backtobasics", broker=broker, backend=backend)

# Celery va chercher automatiquement un fichier tasks.py dans ce package
app.autodiscover_tasks(["src.infrastructure.celery"])
