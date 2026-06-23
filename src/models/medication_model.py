"""
Medication Data Models
Pydantic models for medication management with validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class MedicationType(str, Enum):
    TABLET = "tablet"
    CAPSULE = "capsule"
    LIQUID = "liquid"
    INJECTION = "injection"
    TOPICAL = "topical"

class MedicationFrequency(str, Enum):
    ONCE_DAILY = "once_daily"
    TWICE_DAILY = "twice_daily"
    THREE_TIMES_DAILY = "three_times_daily"
    FOUR_TIMES_DAILY = "four_times_daily"
    AS_NEEDED = "as_needed"

class Medication(BaseModel):
    """Medication model with validation"""
    id: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=200)
    type: MedicationType
    dosage: str = Field(..., regex=r'^\d+\s*(mg|ml|g|mcg)$')
    frequency: MedicationFrequency
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    @validator('name')
    def validate_medication_name(cls, v):
        if not v.strip():
            raise ValueError('Medication name cannot be empty')
        return v.strip()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class MedicationSchedule(BaseModel):
    """Medication schedule model"""
    id: Optional[str] = None
    medication_id: str
    user_id: str
    frequency: MedicationFrequency
    start_date: datetime
    end_date: Optional[datetime] = None
    reminder_times: List[str] = []  # Times in HH:MM format
    reminders_enabled: bool = True
    adherence_rate: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
    
    @validator('reminder_times')
    def validate_reminder_times(cls, v):
        for time_str in v:
            try:
                datetime.strptime(time_str, '%H:%M')
            except ValueError:
                raise ValueError(f'Invalid time format: {time_str}')
        return v
