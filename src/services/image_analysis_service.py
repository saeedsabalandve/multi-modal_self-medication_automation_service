"""
Image Analysis Service
Processes medication images using AWS Rekognition and custom models
"""

import base64
from typing import Dict, Any, List, Optional
from PIL import Image
import io
import asyncio

from src.aws.rekognition_handler import RekognitionHandler
from src.aws.s3_handler import S3Handler
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import ImageProcessingError

class ImageAnalysisService:
    """
    Service for analyzing medication images
    Uses AWS Rekognition for medication identification
    Supports pill, tablet, capsule, and packaging recognition
    """
    
    def __init__(self):
        self.rekognition = RekognitionHandler()
        self.s3_handler = S3Handler()
        self.confidence_threshold = settings.IMAGE_CONFIDENCE_THRESHOLD
    
    async def analyze_medication_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Comprehensive medication image analysis
        Returns detailed medication information
        """
        try:
            # Validate image
            await self._validate_image(image_data)
            
            # Preprocess image
            processed_image = await self._preprocess_image(image_data)
            
            # Detect medication using AWS Rekognition
            rekognition_result = await self._detect_medication(processed_image)
            
            # Extract text from packaging if present
            text_result = await self._extract_text_from_image(processed_image)
            
            # Analyze medication characteristics
            analysis_result = await self._analyze_characteristics(rekognition_result)
            
            return {
                "medication_detected": analysis_result.get("detected", False),
                "medication_name": analysis_result.get("name"),
                "confidence_score": analysis_result.get("confidence", 0),
                "medication_type": analysis_result.get("type"),
                "color": analysis_result.get("color"),
                "shape": analysis_result.get("shape"),
                "imprint": text_result.get("text"),
                "warnings": analysis_result.get("warnings", []),
                "timestamp": analysis_result.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Image analysis failed: {str(e)}")
            raise ImageProcessingError(str(e))
    
    async def identify_pill(self, image_data: bytes) -> Dict[str, Any]:
        """
        Specific pill identification
        Uses shape, color, and imprint recognition
        """
        try:
            # Detect labels with focus on medication
            labels = await self.rekognition.detect_labels(
                image_data,
                max_labels=20,
                min_confidence=80
            )
            
            # Filter medication-related labels
            medication_labels = [
                label for label in labels 
                if any(keyword in label['Name'].lower() 
                      for keyword in ['pill', 'tablet', 'capsule', 'medicine'])
            ]
            
            if not medication_labels:
                return {"detected": False, "message": "No medication detected in image"}
            
            # Get highest confidence medication
            best_match = max(medication_labels, key=lambda x: x['Confidence'])
            
            return {
                "detected": True,
                "label": best_match['Name'],
                "confidence": best_match['Confidence'],
                "categories": [label['Name'] for label in medication_labels[:5]]
            }
            
        except Exception as e:
            logger.error(f"Pill identification failed: {str(e)}")
            raise
    
    async def detect_medication_packaging(self, image_data: bytes) -> Dict[str, Any]:
        """
        Detect medication from packaging/box
        Uses text detection and label recognition
        """
        try:
            # Detect text on packaging
            text_result = await self.rekognition.detect_text(image_data)
            
            # Detect labels
            labels = await self.rekognition.detect_labels(image_data)
            
            # Combine results
            return {
                "text_detected": text_result,
                "labels_detected": labels,
                "packaging_type": self._determine_packaging_type(labels)
            }
            
        except Exception as e:
            logger.error(f"Packaging detection failed: {str(e)}")
            raise
    
    async def _validate_image(self, image_data: bytes):
        """Validate image format and quality"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check image size
            if image.size[0] < 100 or image.size[1] < 100:
                raise ValueError("Image too small for analysis")
            
            # Check file size (max 5MB)
            if len(image_data) > 5 * 1024 * 1024:
                raise ValueError("Image file too large (max 5MB)")
            
            return True
            
        except Exception as e:
            raise ImageProcessingError(f"Invalid image: {str(e)}")
    
    async def _preprocess_image(self, image_data: bytes) -> bytes:
        """
        Preprocess image for better recognition
        Enhance quality, adjust lighting, resize
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large
            max_size = 1024
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            # Save processed image
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return image_data
    
    async def _detect_medication(self, image_data: bytes) -> List[Dict]:
        """Detect medication using AWS Rekognition"""
        return await self.rekognition.detect_labels(
            image_data,
            max_labels=15,
            min_confidence=75
        )
    
    async def _extract_text_from_image(self, image_data: bytes) -> Dict:
        """Extract text from medication packaging"""
        try:
            return await self.rekognition.detect_text(image_data)
        except:
            return {"text": "", "confidence": 0}
    
    async def _analyze_characteristics(self, rekognition_result: List[Dict]) -> Dict:
        """
        Analyze medication characteristics from Rekognition results
        Extract color, shape, type, and other attributes
        """
        # Initialize result
        result = {
            "detected": False,
            "name": None,
            "confidence": 0,
            "type": None,
            "color": None,
            "shape": None,
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Color mapping
        colors = {'red', 'blue', 'white', 'yellow', 'green', 'orange', 'purple', 'pink'}
        shapes = {'round', 'oval', 'capsule', 'oblong', 'square', 'triangle', 'diamond'}
        
        for label in rekognition_result:
            name = label['Name'].lower()
            confidence = label['Confidence']
            
            # Detect medication type
            if 'pill' in name or 'tablet' in name:
                result['type'] = 'tablet'
                result['detected'] = True
                if confidence > result['confidence']:
                    result['confidence'] = confidence
                    result['name'] = label['Name']
            elif 'capsule' in name:
                result['type'] = 'capsule'
                result['detected'] = True
                if confidence > result['confidence']:
                    result['confidence'] = confidence
                    result['name'] = label['Name']
            
            # Detect color
            if name in colors and confidence > 90:
                result['color'] = name
            
            # Detect shape
            if name in shapes and confidence > 85:
                result['shape'] = name
        
        return result
    
    def _determine_packaging_type(self, labels: List[Dict]) -> str:
        """Determine medication packaging type from labels"""
        packaging_keywords = ['bottle', 'box', 'blister', 'pack', 'container']
        
        for label in labels:
            if any(keyword in label['Name'].lower() for keyword in packaging_keywords):
                return label['Name']
        
        return "unknown"

# Required import added at top
from datetime import datetime
