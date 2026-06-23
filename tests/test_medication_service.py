"""
Unit Tests for Medication Service
Tests core medication processing functionality
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.medication_service import MedicationService
from src.models.medication_model import Medication, MedicationType, MedicationFrequency

@pytest.fixture
def medication_service():
    """Fixture for MedicationService instance"""
    with patch('src.aws.s3_handler.S3Handler'), \
         patch('src.aws.rekognition_handler.RekognitionHandler'), \
         patch('src.aws.comprehend_medical_handler.ComprehendMedicalHandler'):
        service = MedicationService()
        return service

@pytest.mark.asyncio
async def test_identify_medication_from_image(medication_service):
    """Test medication identification from image"""
    # Mock Rekognition response
    mock_labels = [
        {'Name': 'Pill', 'Confidence': 99.5},
        {'Name': 'Medicine', 'Confidence': 98.2}
    ]
    
    medication_service.rekognition_handler.detect_labels = AsyncMock(
        return_value=mock_labels
    )
    
    # Test with sample image data
    image_data = b"sample_image_data"
    result = await medication_service.identify_medication_from_image(image_data)
    
    assert result is not None
    assert 'name' in result
    assert 'confidence' in result

@pytest.mark.asyncio
async def test_analyze_prescription_text(medication_service):
    """Test prescription text analysis"""
    # Mock Comprehend Medical response
    mock_entities = {
        'Entities': [
            {
                'Text': 'Aspirin',
                'Category': 'MEDICATION',
                'Type': 'GENERIC_NAME',
                'Score': 0.99
            }
        ]
    }
    
    medication_service.comprehend_handler.detect_entities = AsyncMock(
        return_value=mock_entities
    )
    
    prescription_text = "Take Aspirin 100mg daily"
    result = await medication_service.analyze_prescription_text(prescription_text)
    
    assert result is not None
    assert result.medication_name == "Aspirin"

def test_medication_model_validation():
    """Test medication model validation"""
    # Valid medication
    valid_medication = Medication(
        name="Aspirin",
        type=MedicationType.TABLET,
        dosage="100mg",
        frequency=MedicationFrequency.ONCE_DAILY
    )
    assert valid_medication.name == "Aspirin"
    
    # Invalid dosage format
    with pytest.raises(ValueError):
        Medication(
            name="Invalid",
            type=MedicationType.TABLET,
            dosage="invalid",
            frequency=MedicationFrequency.ONCE_DAILY
  )
