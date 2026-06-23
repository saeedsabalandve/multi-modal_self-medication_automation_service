"""
AWS Service Configuration and Initialization
Manages AWS SDK clients with proper session handling and retry logic
"""

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional
import aioboto3

# Retry configuration for AWS SDK
retry_config = Config(
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    },
    connect_timeout=5,
    read_timeout=60
)

# AWS service clients (lazy initialization)
_s3_client = None
_rekognition_client = None
_comprehend_medical_client = None
_sns_client = None
_dynamodb_client = None
_session = None

async def initialize_aws_services():
    """
    Initialize all AWS service clients
    Uses IAM roles when running on AWS infrastructure
    """
    global _session, _s3_client, _rekognition_client, _comprehend_medical_client
    
    # Create AWS session with credential chain
    _session = aioboto3.Session()
    
    # Initialize core AWS services
    _s3_client = await _session.client('s3', config=retry_config).__aenter__()
    _rekognition_client = await _session.client('rekognition', config=retry_config).__aenter__()
    _comprehend_medical_client = await _session.client('comprehendmedical', config=retry_config).__aenter__()

def get_s3_client():
    """Retrieve S3 client with proper error handling"""
    if not _s3_client:
        raise RuntimeError("AWS services not initialized")
    return _s3_client

def get_rekognition_client():
    """Retrieve Rekognition client for image analysis"""
    if not _rekognition_client:
        raise RuntimeError("AWS Rekognition client not initialized")
    return _rekognition_client
