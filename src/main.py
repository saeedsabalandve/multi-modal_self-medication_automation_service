"""
Main Application Entry Point
Initializes FastAPI application with AWS service integrations
Implements multi-modal self-medication automation workflow
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# AWS Service Initialization
# Initialize AWS clients with latest SDK best practices
from src.config.settings import settings
from src.config.aws_config import initialize_aws_services
from src.api.routes import api_router
from src.utils.logger import setup_logging

# Configure structured logging
logger = setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Handles startup and shutdown events for AWS resources
    """
    # Startup: Initialize AWS services and connection pools
    logger.info("Initializing AWS service connections...")
    await initialize_aws_services()
    logger.info("Multi-Modal Self-Medication Automation Service started")
    
    yield
    
    # Shutdown: Clean up resources and connections
    logger.info("Shutting down service and cleaning up resources...")
    # Cleanup AWS connections and temporary resources

# FastAPI application with comprehensive metadata
app = FastAPI(
    title="Self-Medication Automation Service",
    description="Multi-modal cloud-native medication management using AWS",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v2")

# Health check endpoint for AWS load balancer
@app.get("/health")
async def health_check():
    """Health check endpoint for AWS ELB and monitoring"""
    return {
        "status": "healthy",
        "service": "self-medication-automation",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
)
