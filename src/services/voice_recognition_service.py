"""
Voice Recognition Service
Processes voice input for medication information using AWS Transcribe
"""

import asyncio
from typing import Dict, Any, Optional
import base64
import io
import wave

from src.aws.comprehend_medical_handler import ComprehendMedicalHandler
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import VoiceRecognitionError

class VoiceRecognitionService:
    """
    Service for processing voice-based medication input
    Uses AWS Transcribe for speech-to-text conversion
    Supports multiple languages for medication instructions
    """
    
    def __init__(self):
        self.comprehend_medical = ComprehendMedicalHandler()
        # AWS Transcribe client would be initialized here
        self.supported_languages = ['en-US', 'es-US', 'fr-CA']
        
    async def transcribe_audio(self, audio_data: bytes, language: str = 'en-US') -> str:
        """
        Convert speech to text using AWS Transcribe
        Returns transcribed medication information
        """
        try:
            # Validate audio data
            await self._validate_audio(audio_data)
            
            # Process audio for better recognition
            processed_audio = await self._preprocess_audio(audio_data)
            
            # Simulate AWS Transcribe call (actual implementation would use boto3)
            # In production: use transcribe_client.start_transcription_job()
            transcribed_text = await self._perform_transcription(processed_audio, language)
            
            logger.info(f"Audio transcribed successfully: {transcribed_text[:100]}...")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"Audio transcription failed: {str(e)}")
            raise VoiceRecognitionError(f"Transcription failed: {str(e)}")
    
    async def extract_medication_from_speech(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Complete voice-to-medication pipeline
        Transcribes audio and extracts medication entities
        """
        try:
            # Step 1: Transcribe audio
            text = await self.transcribe_audio(audio_data)
            
            # Step 2: Extract medication entities
            medication_entities = await self.comprehend_medical.detect_entities(text)
            
            # Step 3: Parse medication details
            medication_info = self._parse_medication_entities(medication_entities)
            
            return {
                "transcribed_text": text,
                "medication_detected": medication_info.get("detected", False),
                "medication_name": medication_info.get("name"),
                "dosage": medication_info.get("dosage"),
                "frequency": medication_info.get("frequency"),
                "confidence": medication_info.get("confidence", 0),
                "raw_entities": medication_entities
            }
            
        except Exception as e:
            logger.error(f"Voice medication extraction failed: {str(e)}")
            raise
    
    async def process_voice_command(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process voice commands for medication management
        Supports commands like:
        - "Remind me to take Aspirin at 8 PM"
        - "I took my medication"
        - "What's my next medication?"
        """
        try:
            # Transcribe command
            command_text = await self.transcribe_audio(audio_data)
            
            # Parse intent
            intent = self._detect_command_intent(command_text)
            
            # Extract parameters
            params = self._extract_command_parameters(command_text, intent)
            
            return {
                "command_text": command_text,
                "intent": intent,
                "parameters": params,
                "action": self._determine_action(intent, params)
            }
            
        except Exception as e:
            logger.error(f"Voice command processing failed: {str(e)}")
            raise
    
    async def _validate_audio(self, audio_data: bytes):
        """Validate audio format and quality"""
        try:
            # Check minimum length (at least 1 second of audio)
            if len(audio_data) < 8000:  # Approximate for 8kHz mono
                raise ValueError("Audio too short for recognition")
            
            # Check maximum length (5 minutes)
            if len(audio_data) > 5 * 60 * 16000:  # 5 minutes at 16kHz
                raise ValueError("Audio too long (max 5 minutes)")
            
            return True
            
        except Exception as e:
            raise VoiceRecognitionError(f"Invalid audio: {str(e)}")
    
    async def _preprocess_audio(self, audio_data: bytes) -> bytes:
        """
        Preprocess audio for better recognition
        Noise reduction, format conversion, sample rate adjustment
        """
        try:
            # Convert to WAV format if needed
            # Normalize volume levels
            # Remove silence
            # In production: use audio processing libraries
            
            return audio_data
            
        except Exception as e:
            logger.warning(f"Audio preprocessing failed, using original: {str(e)}")
            return audio_data
    
    async def _perform_transcription(self, audio_data: bytes, language: str) -> str:
        """
        Perform actual transcription
        In production: calls AWS Transcribe API
        """
        # Simulated transcription for demonstration
        # In production, this would use:
        # transcribe_client = boto3.client('transcribe')
        # response = transcribe_client.start_transcription_job(...)
        
        # Mock implementation
        await asyncio.sleep(0.1)  # Simulate API call
        
        # This would be replaced with actual AWS Transcribe response
        return "Take Aspirin 100mg once daily with food"
    
    def _parse_medication_entities(self, entities: Dict) -> Dict:
        """Parse medication entities from Comprehend Medical response"""
        medication_info = {
            "detected": False,
            "name": None,
            "dosage": None,
            "frequency": None,
            "confidence": 0
        }
        
        if 'Entities' not in entities:
            return medication_info
        
        for entity in entities['Entities']:
            category = entity.get('Category', '')
            text = entity.get('Text', '')
            score = entity.get('Score', 0)
            
            if category == 'MEDICATION':
                medication_info['name'] = text
                medication_info['confidence'] = score
                medication_info['detected'] = True
            elif entity.get('Type') == 'DOSAGE':
                medication_info['dosage'] = text
            elif entity.get('Type') == 'FREQUENCY':
                medication_info['frequency'] = text
        
        return medication_info
    
    def _detect_command_intent(self, text: str) -> str:
        """Detect user intent from voice command"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['remind', 'schedule', 'add']):
            return "SCHEDULE_MEDICATION"
        elif any(word in text_lower for word in ['took', 'taken', 'completed']):
            return "LOG_MEDICATION"
        elif any(word in text_lower for word in ['next', 'upcoming', 'schedule']):
            return "CHECK_SCHEDULE"
        elif any(word in text_lower for word in ['missed', 'forgot']):
            return "MISSED_DOSE"
        else:
            return "UNKNOWN"
    
    def _extract_command_parameters(self, text: str, intent: str) -> Dict:
        """Extract parameters from voice command"""
        # Implementation would use NLP to extract:
        # - Medication name
        # - Time
        # - Dosage
        # - Special instructions
        return {
            "medication": "Aspirin",
            "time": "20:00",
            "dosage": "100mg"
        }
    
    def _determine_action(self, intent: str, params: Dict) -> Dict:
        """Determine action based on intent and parameters"""
        actions = {
            "SCHEDULE_MEDICATION": {
                "action": "create_reminder",
                "params": params
            },
            "LOG_MEDICATION": {
                "action": "log_dose",
                "params": {"taken": True, "timestamp": datetime.now().isoformat()}
            },
            "CHECK_SCHEDULE": {
                "action": "get_schedule",
                "params": {}
            },
            "MISSED_DOSE": {
                "action": "handle_missed_dose",
                "params": params
            }
        }
        return actions.get(intent, {"action": "unknown", "params": params})

# Required import
from datetime import datetime
