import io
from locust import HttpUser, task, between


FAKE_IMAGE = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 1024)  # JPEG header 

def _fresh_image():
    # a BytesIO file object has internal cursor and after it has been written, 
    # it is at the end of the file. 
    # So here we reset the cursor to read it again.
    FAKE_IMAGE.seek(0)
    return FAKE_IMAGE

# using HttpUser locust parent class to mock a user
class ImageAPIUser(HttpUser):
    wait_time = between(1, 3)

    @task(2)
    def upload_image(self):
        self.client.post(
            "/images/upload",
            files={"file": ("test.jpg", _fresh_image(), "image/jpeg")},
        )

    @task(1)
    def process_image(self):
        response = self.client.post(
            "/images/process",
            files={"file": ("test.jpg", _fresh_image(), "image/jpeg")},
        )
        if response.status_code == 200:
            task_id = response.json().get("task_id")
            if task_id:
                self.client.get(f"/images/process/{task_id}", name="/images/process/[task_id]")
