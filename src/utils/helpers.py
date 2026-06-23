"""
Utility Helper Functions
Common utilities for medication automation
"""

import hashlib
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import re
import json
from decimal import Decimal

def generate_unique_id() -> str:
    """Generate unique ID for medications and schedules"""
    return str(uuid.uuid4())

def hash_medication_image(image_data: bytes) -> str:
    """Create hash of medication image for deduplication"""
    return hashlib.sha256(image_data).hexdigest()

def parse_medication_dosage(dosage_str: str) -> Dict[str, Any]:
    """
    Parse medication dosage string
    Examples: "100mg", "5ml", "500mcg", "2 tablets"
    """
    dosage_pattern = r'^(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg|tablets?|capsules?|units?)$'
    match = re.match(dosage_pattern, dosage_str.lower().strip())
    
    if not match:
        return {"value": None, "unit": None, "original": dosage_str}
    
    return {
        "value": float(match.group(1)),
        "unit": match.group(2),
        "original": dosage_str
    }

def calculate_next_dose_time(
    frequency: str, 
    last_dose_time: Optional[datetime] = None
) -> datetime:
    """
    Calculate next medication dose time based on frequency
    """
    if not last_dose_time:
        last_dose_time = datetime.now()
    
    frequency_hours = {
        'once_daily': 24,
        'twice_daily': 12,
        'three_times_daily': 8,
        'four_times_daily': 6
    }
    
    hours = frequency_hours.get(frequency, 24)
    return last_dose_time + timedelta(hours=hours)

def format_medication_reminder(medication_name: str, dosage: str, time: datetime) -> str:
    """
    Format medication reminder message
    """
    time_str = time.strftime("%I:%M %p")
    return f"🔔 Time to take {medication_name} ({dosage}) at {time_str}"

def calculate_adherence_rate(
    total_doses: int, 
    taken_doses: int
) -> float:
    """
    Calculate medication adherence rate as percentage
    """
    if total_doses == 0:
        return 0.0
    
    rate = (taken_doses / total_doses) * 100
    return round(min(100, max(0, rate)), 2)

def sanitize_medication_name(name: str) -> str:
    """
    Sanitize medication name for storage
    """
    # Remove special characters
    sanitized = re.sub(r'[^\w\s-]', '', name)
    # Normalize whitespace
    sanitized = ' '.join(sanitized.split())
    # Title case
    return sanitized.title()

def is_valid_medication_time(time_str: str) -> bool:
    """
    Validate medication time format (HH:MM)
    """
    try:
        datetime.strptime(time_str, '%H:%M')
        return True
    except ValueError:
        return False

def serialize_dynamodb_item(item: Dict) -> Dict:
    """
    Serialize Python dict to DynamoDB format
    """
    serialized = {}
    for key, value in item.items():
        if isinstance(value, str):
            serialized[key] = {'S': value}
        elif isinstance(value, (int, float, Decimal)):
            serialized[key] = {'N': str(value)}
        elif isinstance(value, bool):
            serialized[key] = {'BOOL': value}
        elif isinstance(value, list):
            if all(isinstance(x, str) for x in value):
                serialized[key] = {'SS': value}
            else:
                serialized[key] = {'L': [serialize_dynamodb_item({'v': v})['v'] for v in value]}
        elif isinstance(value, dict):
            serialized[key] = {'M': serialize_dynamodb_item(value)}
        elif value is None:
            serialized[key] = {'NULL': True}
    return serialized

def deserialize_dynamodb_item(item: Dict) -> Dict:
    """
    Deserialize DynamoDB item to Python dict
    """
    deserialized = {}
    for key, value in item.items():
        if 'S' in value:
            deserialized[key] = value['S']
        elif 'N' in value:
            deserialized[key] = float(value['N']) if '.' in value['N'] else int(value['N'])
        elif 'BOOL' in value:
            deserialized[key] = value['BOOL']
        elif 'SS' in value:
            deserialized[key] = value['SS']
        elif 'L' in value:
            deserialized[key] = [deserialize_dynamodb_item({'v': v})['v'] for v in value['L']]
        elif 'M' in value:
            deserialized[key] = deserialize_dynamodb_item(value['M'])
        elif 'NULL' in value:
            deserialized[key] = None
    return deserialized

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def mask_sensitive_data(data: Dict, fields: List[str] = None) -> Dict:
    """
    Mask sensitive information in data for logging
    """
    if fields is None:
        fields = ['password', 'token', 'secret', 'api_key']
    
    masked = data.copy()
    for field in fields:
        if field in masked:
            masked[field] = '***MASKED***'
    
    return masked

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, phone))
