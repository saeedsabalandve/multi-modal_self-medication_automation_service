"""
API Request Validators
Input validation for medication automation endpoints
"""

from pydantic import BaseModel, Field, validator, ValidationError
from typing import Optional, List, Union
from datetime import datetime
import re
from fastapi import HTTPException

class MedicationImageRequest(BaseModel):
    """Validate medication image upload request"""
    user_id: str = Field(..., min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('user_id')
    def validate_user_id(cls, v):
        if not v.strip():
            raise ValueError('User ID cannot be empty')
        return v.strip()

class MedicationVoiceRequest(BaseModel):
    """Validate medication voice input request"""
    user_id: str = Field(..., min_length=3, max_length=50)
    language: str = Field(default='en-US', regex=r'^[a-z]{2}-[A-Z]{2}$')
    
    @validator('language')
    def validate_language(cls, v):
        supported = ['en-US', 'es-US', 'fr-CA', 'de-DE']
        if v not in supported:
            raise ValueError(f'Language must be one of {supported}')
        return v

class MedicationTextRequest(BaseModel):
    """Validate medication text prescription request"""
    user_id: str = Field(..., min_length=3, max_length=50)
    prescription_text: str = Field(..., min_length=10, max_length=1000)
    
    @validator('prescription_text')
    def validate_prescription(cls, v):
        if not any(keyword in v.lower() for keyword in ['take', 'mg', 'ml', 'daily', 'times']):
            raise ValueError('Text does not appear to contain medication instructions')
        return v.strip()

class MedicationScheduleRequest(BaseModel):
    """Validate medication schedule creation request"""
    user_id: str = Field(..., min_length=3, max_length=50)
    medication_name: str = Field(..., min_length=2, max_length=200)
    dosage: str = Field(..., regex=r'^\d+\s*(mg|ml|g|mcg|units?)$')
    frequency: str = Field(..., regex=r'^(once_daily|twice_daily|three_times_daily|four_times_daily|as_needed)$')
    duration_days: int = Field(..., ge=1, le=365)
    reminder_times: Optional[List[str]] = None
    
    @validator('reminder_times')
    def validate_reminder_times(cls, v):
        if v:
            for time_str in v:
                if not re.match(r'^([01]\d|2[0-3]):([0-5]\d)$', time_str):
                    raise ValueError(f'Invalid time format: {time_str}. Use HH:MM')
        return v

class MedicationLogRequest(BaseModel):
    """Validate medication logging request"""
    schedule_id: str = Field(..., min_length=5, max_length=100)
    taken: bool = True
    timestamp: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)

async def validate_medication_input(data: dict, input_type: str):
    """
    Validate medication input based on type
    Raises HTTPException for invalid input
    """
    validators_map = {
        'image': MedicationImageRequest,
        'voice': MedicationVoiceRequest,
        'text': MedicationTextRequest,
        'schedule': MedicationScheduleRequest,
        'log': MedicationLogRequest
    }
    
    validator_class = validators_map.get(input_type)
    if not validator_class:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input type: {input_type}"
        )
    
    try:
        validated_data = validator_class(**data)
        return validated_data.dict()
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
)
