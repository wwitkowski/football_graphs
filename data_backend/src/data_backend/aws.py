import json
import os
from io import BytesIO
from typing import Any

import boto3


class S3Client:
    """Encapsulates S3 client."""

    def __init__(self, bucket: str):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url="https://localhost:9000",
            aws_access_key_id=os.environ.get("ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("ACCESS_KEY"),
        )
        self.bucket = bucket

    def upload_json(self, data: dict[str, Any], key: str):
        """Uploads JSON data to S3."""
        json_bytes = json.dumps(data).encode("utf-8")
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=BytesIO(json_bytes),
            ContentType="application/json",
        )
