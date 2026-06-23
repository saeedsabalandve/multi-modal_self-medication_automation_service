"""
User Data Models
Patient/user profiles for medication management
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

class UserRole(str, Enum):
    PATIENT = "patient"
    CAREGIVER = "caregiver"
    DOCTOR = "doctor"
    ADMIN = "admin"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class User(BaseModel):
    """User/Patient model for medication tracking"""
    id: Optional[str] = None
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, regex=r'^\+?1?\d{9,15}$')
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    role: UserRole = UserRole.PATIENT
    medical_conditions: List[str] = []
    allergies: List[str] = []
    active_medications: List[str] = []
    caregiver_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    @validator('allergies')
    def validate_allergies(cls, v):
        """Clean and deduplicate allergies list"""
        return list(set([allergy.strip().lower() for allergy in v if allergy.strip()]))
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }

class UserProfile(BaseModel):
    """Extended user profile with medication history"""
    user: User
    medication_history: List[dict] = []
    adherence_rate: float = Field(default=0.0, ge=0, le=100)
    total_medications: int = 0
    missed_doses: int = 0
    last_medication_taken: Optional[datetime] = None
