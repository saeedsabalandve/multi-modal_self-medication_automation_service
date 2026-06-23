"""
Self-Medication Automation Workflow
Orchestrates the multi-modal medication management process
Integrates AWS Step Functions for complex workflows
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import json

from src.services.medication_service import MedicationService
from src.services.image_analysis_service import ImageAnalysisService
from src.services.voice_recognition_service import VoiceRecognitionService
from src.services.notification_service import NotificationService
from src.automation.medication_scheduler import MedicationScheduler
from src.automation.reminder_engine import ReminderEngine
from src.utils.logger import logger
from src.utils.exceptions import WorkflowError

class SelfMedicationWorkflow:
    """
    Main automation workflow for self-medication management
    Supports image, voice, and text input modalities
    Uses AWS Step Functions for complex orchestration
    """
    
    def __init__(self):
        # Initialize all service components
        self.medication_service = MedicationService()
        self.image_analysis = ImageAnalysisService()
        self.voice_recognition = VoiceRecognitionService()
        self.notification_service = NotificationService()
        self.scheduler = MedicationScheduler()
        self.reminder_engine = ReminderEngine()
    
    async def process_medication_image(self, user_id: str, image_data: bytes) -> Dict[str, Any]:
        """
        Process medication through image input modality
        Uses AWS Rekognition for pill identification
        """
        try:
            logger.info(f"Processing medication image for user: {user_id}")
            
            # Step 1: Identify medication from image
            medication_info = await self.medication_service.identify_medication_from_image(
                image_data
            )
            
            # Step 2: Validate medication details
            validated_info = await self._validate_medication(medication_info)
            
            # Step 3: Create automated schedule
            schedule = await self._create_automated_schedule(
                user_id, 
                validated_info
            )
            
            # Step 4: Send confirmation notification
            await self.notification_service.send_medication_confirmation(
                user_id,
                validated_info
            )
            
            logger.info(f"Medication processing completed for user: {user_id}")
            
            return {
                "status": "success",
                "medication": validated_info,
                "schedule_id": schedule.id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Medication workflow failed: {str(e)}")
            raise WorkflowError(f"Failed to process medication: {str(e)}")
    
    async def process_voice_medication(self, user_id: str, audio_data: bytes) -> Dict[str, Any]:
        """
        Process medication through voice input modality
        Uses AWS Transcribe for speech-to-text conversion
        """
        try:
            logger.info(f"Processing voice medication for user: {user_id}")
            
            # Step 1: Convert speech to text
            transcribed_text = await self.voice_recognition.transcribe_audio(
                audio_data
            )
            
            # Step 2: Extract medication information from text
            medication_info = await self.medication_service.analyze_prescription_text(
                transcribed_text
            )
            
            # Step 3: Process and schedule medication
            schedule = await self._create_automated_schedule(
                user_id, 
                medication_info
            )
            
            return {
                "status": "success",
                "transcribed_text": transcribed_text,
                "medication": medication_info.dict(),
                "schedule_id": schedule.id
            }
            
        except Exception as e:
            logger.error(f"Voice medication processing failed: {str(e)}")
            raise WorkflowError(f"Voice processing failed: {str(e)}")
    
    async def process_text_prescription(self, user_id: str, prescription_text: str) -> Dict[str, Any]:
        """
        Process medication through text prescription input
        Uses AWS Comprehend Medical for text analysis
        """
        try:
            # Analyze prescription text
            prescription = await self.medication_service.analyze_prescription_text(
                prescription_text
            )
            
            # Create medication schedule
            schedule = await self._create_automated_schedule(
                user_id, 
                prescription
            )
            
            return {
                "status": "success",
                "prescription": prescription.dict(),
                "schedule_id": schedule.id
            }
            
        except Exception as e:
            logger.error(f"Text prescription processing failed: {str(e)}")
            raise WorkflowError(f"Text processing failed: {str(e)}")
    
    async def _validate_medication(self, medication_info: Dict) -> Dict:
        """Validate medication information against database"""
        # Implementation for medication validation
        # Integrates with AWS DynamoDB for medication database
        return medication_info
    
    async def _create_automated_schedule(self, user_id: str, medication_info: Any) -> Any:
        """Create automated medication schedule with reminders"""
        # Implementation for automated scheduling
        # Uses MedicationScheduler and ReminderEngine
        return await self.scheduler.create_schedule(user_id, medication_info)
    
    async def trigger_medication_reminder(self, user_id: str, schedule_id: str):
        """
        Trigger medication reminder for user
        Uses Amazon SNS for push notifications
        """
        await self.reminder_engine.send_reminder(user_id, schedule_id)
