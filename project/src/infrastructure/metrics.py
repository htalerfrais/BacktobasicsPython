from prometheus_client import Counter, Histogram

CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "End-to-end duration of process_image_task",
    buckets=[1, 2, 5, 10, 20, 30, 60],
)

CELERY_TASKS_TOTAL = Counter(
    "celery_tasks_total",
    "Total Celery tasks completed, by status",
    ["status"],
)

ML_INFERENCE_DURATION = Histogram(
    "ml_inference_duration_seconds",
    "DeepLabV3 forward pass only",
    buckets=[0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30],
)

ML_MASK_CONFIDENCE = Histogram(
    "ml_mask_confidence",
    "Mean softmax confidence on foreground (non-background) pixels",
    buckets=[0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0],
)
