import json
from io import BytesIO
from typing import Any

import boto3


class S3Client:
    """Encapsulates S3 client."""

    def __init__(self, bucket: str):
        self.s3_client = boto3.client("s3", endpoint_url="http://minio:9000")
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
