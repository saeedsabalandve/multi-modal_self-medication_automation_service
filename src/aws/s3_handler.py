"""
AWS S3 Handler Module
Manages S3 operations for medication storage and retrieval
"""

import boto3
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import asyncio
from src.config.settings import settings
from src.utils.logger import logger

class S3Handler:
    """Handler for AWS S3 operations"""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION,
            config=boto3.session.Config(
                signature_version='s3v4',
                retries={'max_attempts': 3}
            )
        )
        self.bucket_name = settings.S3_BUCKET_NAME
    
    async def upload_file(self, file_data: bytes, key: str, content_type: str = 'image/jpeg') -> str:
        """
        Upload file to S3 bucket
        Returns the S3 URI of uploaded file
        """
        try:
            await asyncio.to_thread(
                self.s3_client.put_object,
                Bucket=self.bucket_name,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ServerSideEncryption='AES256'
            )
            
            file_url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"File uploaded successfully: {file_url}")
            return file_url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {str(e)}")
            raise
    
    async def download_file(self, key: str) -> bytes:
        """Download file from S3 bucket"""
        try:
            response = await asyncio.to_thread(
                self.s3_client.get_object,
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {str(e)}")
            raise
    
    async def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate presigned URL for temporary access"""
        try:
            url = await asyncio.to_thread(
                self.s3_client.generate_presigned_url,
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise
    
    async def delete_file(self, key: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            await asyncio.to_thread(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=key
            )
            logger.info(f"File deleted: {key}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file: {str(e)}")
            return False
