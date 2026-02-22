import json
from typing import Any

import boto3


class S3Client:
    """
    A simple wrapper around the boto3 S3 client for saving JSON objects.

    Provides convenience methods for interacting with S3, such as saving
    Python dictionaries as JSON files.
    """

    def __init__(self, bucket_name: str = "raw-data", endpoint: str | None = None):
        """
        Initialize the S3 client.

        Parameters
        ----------
        bucket_name : str, optional
            The name of the S3 bucket. Default is ``"raw-data"``.
        endpoint : str or None, optional
            The endpoint URL for the S3 service. Useful for connecting
            to local or non-AWS S3-compatible services (e.g., MinIO).
            Default is ``None``.
        """
        self.s3_client = boto3.client("s3", endpoint_url=endpoint)
        self.bucket_name = bucket_name

    def save_json(self, data: dict[str, Any], key: str):
        """
        Save a dictionary as a JSON object in the configured S3 bucket.

        Parameters
        ----------
        data : dict of (str, Any)
            The dictionary to serialize as JSON and upload.
        key : str
            The object key (path/filename) under which the JSON
            will be stored in the S3 bucket.
        """
        json_bytes = json.dumps(data)
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=json_bytes.encode("utf-8"),
            ContentType="application/json",
        )
