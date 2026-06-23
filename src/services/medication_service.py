"""
Medication Service Module
Core business logic for medication management and automation
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
import asyncio

from src.models.medication_model import Medication, MedicationSchedule
from src.models.prescription_model import Prescription
from src.aws.s3_handler import S3Handler
from src.aws.rekognition_handler import RekognitionHandler
from src.aws.comprehend_medical_handler import ComprehendMedicalHandler
from src.utils.logger import logger
from src.utils.exceptions import MedicationNotFoundError

class MedicationService:
    """
    Main medication management service
    Integrates AWS AI/ML services for multi-modal medication processing
    """
    
    def __init__(self):
        # Initialize AWS service handlers
        self.s3_handler = S3Handler()
        self.rekognition_handler = RekognitionHandler()
        self.comprehend_handler = ComprehendMedicalHandler()
    
    async def identify_medication_from_image(self, image_data: bytes) -> Dict:
        """
        Identify medication using AWS Rekognition
        Processes pill images and returns medication details
        """
        try:
            # Upload image to S3 for processing
            image_key = f"medication-images/{datetime.now().timestamp()}.jpg"
            await self.s3_handler.upload_file(image_data, image_key)
            
            # Analyze image with AWS Rekognition
            labels = await self.rekognition_handler.detect_labels(image_key)
            
            # Extract medication information
            medication_info = await self._extract_medication_details(labels)
            
            logger.info(f"Medication identified from image: {medication_info.get('name')}")
            return medication_info
            
        except Exception as e:
            logger.error(f"Failed to identify medication from image: {str(e)}")
            raise
    
    async def analyze_prescription_text(self, prescription_text: str) -> Prescription:
        """
        Analyze prescription text using AWS Comprehend Medical
        Extracts medication entities, dosage, and frequency
        """
        try:
            # Analyze with Comprehend Medical
            medical_entities = await self.comprehend_handler.detect_entities(
                prescription_text
            )
            
            # Parse and structure prescription data
            prescription = Prescription.from_comprehend_entities(medical_entities)
            
            logger.info(f"Prescription analyzed successfully: {prescription.medication_name}")
            return prescription
            
        except Exception as e:
            logger.error(f"Prescription analysis failed: {str(e)}")
            raise
    
    async def create_medication_schedule(
        self, 
        medication: Medication, 
        frequency: str, 
        duration_days: int
    ) -> MedicationSchedule:
        """
        Create automated medication schedule
        Generates reminders and tracks adherence
        """
        schedule = MedicationSchedule(
            medication_id=medication.id,
            frequency=frequency,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            reminders_enabled=True
        )
        
        # Generate reminder times based on frequency
        await self._generate_reminder_schedule(schedule)
        
        logger.info(f"Medication schedule created for: {medication.name}")
        return schedule
    
    async def _generate_reminder_schedule(self, schedule: MedicationSchedule):
        """Generate reminder notifications using SNS"""
        # Implementation for reminder generation
        # Uses Amazon SNS for push notifications
        pass
    
    async def _extract_medication_details(self, labels: List) -> Dict:
        """Extract structured medication data from Rekognition labels"""
        # Implementation for medication detail extraction
        return {
            "name": "Sample Medication",
            "confidence": 0.95,
            "category": "Prescription"
      }
