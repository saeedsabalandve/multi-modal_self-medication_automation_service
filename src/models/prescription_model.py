"""
Prescription Data Models
Structured prescription data from AWS Comprehend Medical
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, date
from enum import Enum

class PrescriptionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class MedicationEntity(BaseModel):
    """Individual medication entity from prescription"""
    name: str
    category: str  # MEDICATION, DOSAGE, FREQUENCY, etc.
    type: str  # GENERIC_NAME, BRAND_NAME, etc.
    score: float = Field(ge=0, le=1)
    traits: List[Dict] = []

class Prescription(BaseModel):
    """Complete prescription model"""
    id: Optional[str] = None
    patient_id: str
    doctor_name: Optional[str] = None
    doctor_license: Optional[str] = None
    medication_name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    instructions: Optional[str] = None
    date_prescribed: date = Field(default_factory=date.today)
    expiry_date: Optional[date] = None
    status: PrescriptionStatus = PrescriptionStatus.ACTIVE
    raw_text: Optional[str] = None
    entities: List[MedicationEntity] = []
    aws_confidence_score: float = Field(default=0.0, ge=0, le=1)
    created_at: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def from_comprehend_entities(cls, entities_data: Dict) -> 'Prescription':
        """
        Create Prescription from AWS Comprehend Medical response
        Extracts structured data from medical entities
        """
        entities = []
        medication_name = ""
        dosage = None
        frequency = None
        
        for entity in entities_data.get('Entities', []):
            entity_obj = MedicationEntity(
                name=entity.get('Text', ''),
                category=entity.get('Category', ''),
                type=entity.get('Type', ''),
                score=entity.get('Score', 0),
                traits=entity.get('Traits', [])
            )
            entities.append(entity_obj)
            
            # Extract key information
            if entity.get('Category') == 'MEDICATION':
                medication_name = entity.get('Text', '')
            elif entity.get('Type') == 'DOSAGE':
                dosage = entity.get('Text', '')
            elif entity.get('Type') == 'FREQUENCY':
                frequency = entity.get('Text', '')
        
        return cls(
            patient_id="",  # Will be set by caller
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            entities=entities,
            aws_confidence_score=0.95  # Default confidence
        )
    
    @validator('duration_days')
    def validate_duration(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Duration must be positive')
        if v is not None and v > 365:
            raise ValueError('Duration cannot exceed 1 year')
        return v
