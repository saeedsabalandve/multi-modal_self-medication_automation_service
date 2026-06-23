"""
API Routes Definition
FastAPI routes for medication automation endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio

from src.services.medication_service import MedicationService
from src.automation.self_medication_workflow import SelfMedicationWorkflow
from src.models.medication_model import Medication, MedicationSchedule
from src.api.validators import validate_medication_input
from src.utils.logger import logger

api_router = APIRouter()
medication_service = MedicationService()
workflow = SelfMedicationWorkflow()

@api_router.post("/medication/image", response_model=Dict[str, Any])
async def process_medication_image(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Process medication through image upload
    Uses AWS Rekognition for pill identification
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read image data
        image_data = await file.read()
        
        # Process through workflow
        result = await workflow.process_medication_image(user_id, image_data)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": "Medication identified successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/medication/voice", response_model=Dict[str, Any])
async def process_voice_medication(
    user_id: str,
    file: UploadFile = File(...)
):
    """
    Process medication through voice input
    Uses AWS Transcribe for speech-to-text
    """
    try:
        # Validate audio file
        if not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be audio")
        
        audio_data = await file.read()
        result = await workflow.process_voice_medication(user_id, audio_data)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": "Voice medication processed"
            }
        )
        
    except Exception as e:
        logger.error(f"Voice processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/medication/text", response_model=Dict[str, Any])
async def process_text_prescription(
    user_id: str,
    prescription_text: str
):
    """
    Process medication through text prescription
    Uses AWS Comprehend Medical for analysis
    """
    try:
        result = await workflow.process_text_prescription(user_id, prescription_text)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": result,
                "message": "Prescription processed successfully"
            }
        )
        
    except Exception as e:
        logger.error(f"Text processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/medication/schedule/{user_id}")
async def get_medication_schedule(user_id: str):
    """Get medication schedule for user"""
    try:
        schedules = await medication_service.get_user_schedules(user_id)
        return {
            "success": True,
            "data": schedules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/medication/reminder/{schedule_id}/trigger")
async def trigger_reminder(schedule_id: str, user_id: str):
    """Manually trigger medication reminder"""
    try:
        await workflow.trigger_medication_reminder(user_id, schedule_id)
        return {
            "success": True,
            "message": "Reminder triggered successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/health")
async def health_check():
    """API health check endpoint"""
    return {
        "status": "healthy",
        "service": "self-medication-automation-api",
        "version": "2.0.0"
    }
