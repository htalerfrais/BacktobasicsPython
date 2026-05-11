import mimetypes
import random
import uuid
from pathlib import Path

from locust import HttpUser, between, task

ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "coco_samples"
SUPPORTED_EXTENSIONS = ("*.jpg", "*.jpeg", "*.png", "*.webp")


def _list_images() -> list[Path]:
    images: list[Path] = []
    for pattern in SUPPORTED_EXTENSIONS:
        images.extend(ASSETS_DIR.glob(pattern))
    return images


IMAGE_POOL = _list_images()
if not IMAGE_POOL:
    raise RuntimeError(
        f"No load-test images found in {ASSETS_DIR}. "
        "Download sample images before running Locust."
    )

class ImageAPIUser(HttpUser):
    # Short think-time to create sustained pressure on API + Celery worker.
    wait_time = between(0.1, 0.5)

    @task
    def process_image(self):
        image_path = random.choice(IMAGE_POOL)
        content_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        request_name = f"{uuid.uuid4().hex}_{image_path.name}"
        self.client.post(
            "/images/process",
            files={"file": (request_name, image_path.read_bytes(), content_type)},
        )
