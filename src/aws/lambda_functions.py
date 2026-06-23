"""
AWS Lambda Functions for Serverless Components
Implements serverless handlers for medication automation
"""

import json
import boto3
from typing import Dict, Any
from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize AWS Lambda Powertools
logger = Logger()
tracer = Tracer()
metrics = Metrics()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def medication_image_processor(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda function for processing medication images
    Triggered by S3 upload events
    Integrates with AWS Rekognition for image analysis
    """
    logger.info("Processing medication image upload event")
    
    try:
        # Extract S3 event details
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Initialize AWS clients
        rekognition = boto3.client('rekognition')
        sns = boto3.client('sns')
        
        # Detect medication labels in image
        response = rekognition.detect_labels(
            Image={'S3Object': {'Bucket': bucket, 'Name': key}},
            MaxLabels=10,
            MinConfidence=85
        )
        
        # Process labels and identify medication
        medication_detected = process_medication_labels(response['Labels'])
        
        # Send notification if medication identified
        if medication_detected:
            sns.publish(
                TopicArn=os.environ['SNS_TOPIC_ARN'],
                Message=json.dumps({
                    'medication': medication_detected,
                    'image_key': key,
                    'timestamp': context.aws_request_id
                })
            )
        
        logger.info(f"Medication processing completed for: {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Medication processed successfully',
                'medication': medication_detected
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing medication image: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def medication_reminder_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda function for medication reminders
    Scheduled via CloudWatch Events
    Sends notifications through Amazon SNS
    """
    logger.info("Processing medication reminders")
    
    try:
        # Query DynamoDB for active medication schedules
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        response = table.scan(
            FilterExpression='reminder_enabled = :enabled',
            ExpressionAttributeValues={':enabled': True}
        )
        
        # Process each active schedule
        sns = boto3.client('sns')
        reminders_sent = 0
        
        for item in response['Items']:
            if should_send_reminder(item):
                # Send reminder notification
                sns.publish(
                    TopicArn=os.environ['SNS_TOPIC_ARN'],
                    Message=json.dumps({
                        'user_id': item['user_id'],
                        'medication': item['medication_name'],
                        'dosage': item['dosage'],
                        'reminder_type': 'medication_time'
                    })
                )
                reminders_sent += 1
        
        logger.info(f"Sent {reminders_sent} medication reminders")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'reminders_sent': reminders_sent,
                'timestamp': context.aws_request_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error sending reminders: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def process_medication_labels(labels: list) -> Dict[str, Any]:
    """Process AWS Rekognition labels to identify medication"""
    # Implementation for label processing
    medication_keywords = ['pill', 'tablet', 'capsule', 'medicine', 'medication']
    
    for label in labels:
        if any(keyword in label['Name'].lower() for keyword in medication_keywords):
            return {
                'detected': True,
                'label': label['Name'],
                'confidence': label['Confidence']
            }
    
    return {'detected': False}

def should_send_reminder(item: Dict) -> bool:
    """Check if reminder should be sent based on schedule"""
    # Implementation for reminder scheduling logic
    return True
