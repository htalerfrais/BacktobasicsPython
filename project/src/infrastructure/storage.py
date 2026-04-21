import os
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from src.domain.interfaces import StoragePort
from src.domain.models import ImageMetadata


class S3Storage(StoragePort):
    """Implémentation S3-compatible du port de stockage.
    
    Fonctionne avec MinIO (dev/local) et AWS S3 (prod) via boto3.
    Configuration par variables d'environnement.
    """

    def __init__(self):
        self.bucket = os.environ["MINIO_BUCKET"]
        self._client = boto3.client(
            "s3",
            endpoint_url=os.environ["MINIO_ENDPOINT"],
            aws_access_key_id=os.environ["MINIO_ROOT_USER"],
            aws_secret_access_key=os.environ["MINIO_ROOT_PASSWORD"],
            region_name="us-east-1",  # MinIO ignore la région, boto3 l'exige quand même
        )

    def save(self, data: bytes, key: str) -> ImageMetadata:
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentLength=len(data),
        )
        filename = Path(key).name
        return ImageMetadata(
            filename=filename,
            file_extension=Path(filename).suffix.lower().lstrip("."),
            size_bytes=len(data),
            object_key=key,
        )

    def get(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            raise FileNotFoundError(f"Objet introuvable dans le bucket : {key}") from e
