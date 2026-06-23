"""
Application Configuration Settings
Environment-based configuration following 12-factor app principles
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    Supports AWS Secrets Manager integration for sensitive data
    """
    
    # Application Settings
    APP_NAME: str = "self-medication-automation"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    
    # AWS Service Configuration
    S3_BUCKET_NAME: str = "self-medication-storage"
    DYNAMODB_TABLE: str = "medication-records"
    SNS_TOPIC_ARN: Optional[str] = None
    REKOGNITION_COLLECTION_ID: str = "medication-images"
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Model Settings
    MEDICATION_MODEL_PATH: str = "models/medication_classifier.pkl"
    IMAGE_CONFIDENCE_THRESHOLD: float = 0.85
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
