import io
import uuid
from locust import HttpUser, task, constant
from PIL import Image
import time


def create_test_image():
    img = Image.new("RGB", (100, 100), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

class ImageAPIUser(HttpUser):
    wait_time = constant(1)
        
    @task
    def process_image(self):
        img = create_test_image()
        name = f"test_{uuid.uuid4().hex}.png"
        self.client.post(
            "/images/process",
            files={"file": (name, img, "image/png")},
        )
