"""
Custom Exception Classes
Domain-specific exceptions for medication automation
"""

class MedicationAutomationError(Exception):
    """Base exception for medication automation"""
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class MedicationNotFoundError(MedicationAutomationError):
    """Exception raised when medication is not found"""
    def __init__(self, medication_id: str):
        super().__init__(
            message=f"Medication not found: {medication_id}",
            error_code="MEDICATION_NOT_FOUND"
        )

class ImageProcessingError(MedicationAutomationError):
    """Exception raised for image processing failures"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Image processing failed: {message}",
            error_code="IMAGE_PROCESSING_ERROR"
        )

class VoiceRecognitionError(MedicationAutomationError):
    """Exception raised for voice recognition failures"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Voice recognition failed: {message}",
            error_code="VOICE_RECOGNITION_ERROR"
        )

class WorkflowError(MedicationAutomationError):
    """Exception raised for workflow execution failures"""
    def __init__(self, message: str):
        super().__init__(
            message=f"Workflow execution failed: {message}",
            error_code="WORKFLOW_ERROR"
        )

class AWSIntegrationError(MedicationAutomationError):
    """Exception raised for AWS service integration failures"""
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"AWS {service} error: {message}",
            error_code=f"AWS_{service.upper()}_ERROR"
                         )
