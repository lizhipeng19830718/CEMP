import io
import os
from typing import Dict, Union, Any

from chainlit.data.base import BaseStorageClient
from chainlit.logger import logger
from minio import Minio

class MinioStorageClient(BaseStorageClient):

    def __init__(self):
        try:
            self.client = Minio(endpoint=os.environ["MINIO_ENDPOINT"], access_key=os.getenv("MINIO_ACCESS_KEY"), secret_key=os.getenv("MINIO_SECRET_KEY"), secure=False)
            logger.info("MinioStorageClient initialized")
        except Exception as e:
            logger.warn(f"MinioStorageClient initialization error: {e}")

    async def upload_file(self, object_key: str, data: Union[bytes, str], mime: str = 'application/octet-stream',
                          overwrite: bool = True) -> Dict[str, Any]:
        try:
            if isinstance(data, str):
                data = io.BytesIO(data.encode('utf-8'))
            else:
                data = io.BytesIO(data)
            bucket_name = os.getenv("MINIO_BUCKET_NAME", "danwen")
            self.client.put_object(bucket_name=bucket_name, object_name=object_key, data=data, length=len(data.getvalue()), content_type=mime)
            # get file url from minio
            url = self.client.get_presigned_url("GET", bucket_name, object_key)
            return {"object_key": object_key, "url": url}
        except Exception as e:
            logger.warn(f"MinioStorageClient, upload_file error: {e}")
            return {}

