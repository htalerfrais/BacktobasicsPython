import io
from locust import HttpUser, task, between

# Crée une vraie image PNG minimale en mémoire
def create_test_image():
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

class ImageAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def upload_image(self):
        img = create_test_image()
        self.client.post(
            "/images/upload",
            files={"file": ("test.png", img, "image/png")},
        )

    @task(1)
    def process_image(self):
        img = create_test_image()
        response = self.client.post(
            "/images/process",
            files={"file": ("test.png", img, "image/png")},
        )
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            if task_id:
                self.client.get(f"/images/process/{task_id}", name="/images/process/[task_id]")