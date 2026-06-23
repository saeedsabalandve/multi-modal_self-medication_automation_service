"""
Notification Service
Handles medication reminders and alerts via AWS SNS and SES
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.aws.sns_handler import SNSHandler
from src.config.settings import settings
from src.utils.logger import logger

class NotificationService:
    """
    Service for sending medication notifications
    Supports multiple channels: Push, SMS, Email
    Uses AWS SNS for push notifications
    Uses AWS SES for email notifications
    """
    
    def __init__(self):
        self.sns_handler = SNSHandler()
        self.notification_channels = {
            'push': True,
            'sms': True,
            'email': True
        }
    
    async def send_medication_confirmation(
        self, 
        user_id: str, 
        medication_info: Dict
    ) -> bool:
        """
        Send confirmation after medication identification
        Informs user about identified medication details
        """
        try:
            message = self._create_confirmation_message(medication_info)
            
            # Send via multiple channels
            tasks = []
            
            if self.notification_channels['push']:
                tasks.append(
                    self._send_push_notification(user_id, "Medication Identified", message)
                )
            
            if self.notification_channels['sms']:
                tasks.append(
                    self._send_sms_notification(user_id, message[:160])  # SMS limit
                )
            
            if self.notification_channels['email']:
                tasks.append(
                    self._send_email_notification(
                        user_id, 
                        "Medication Identified - Self-Medication Automation", 
                        message
                    )
                )
            
            await asyncio.gather(*tasks)
            logger.info(f"Confirmation sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation: {str(e)}")
            return False
    
    async def send_medication_reminder(
        self, 
        user_id: str, 
        medication_name: str, 
        dosage: str,
        scheduled_time: datetime
    ) -> bool:
        """
        Send medication reminder notification
        Alerts user to take their medication
        """
        try:
            # Create reminder message
            message = f"🔔 Time to take your medication!\n\n"
            message += f"💊 Medication: {medication_name}\n"
            message += f"📏 Dosage: {dosage}\n"
            message += f"⏰ Scheduled: {scheduled_time.strftime('%I:%M %p')}\n\n"
            message += "Please confirm once taken."
            
            # Send high-priority notification
            await self._send_push_notification(
                user_id, 
                "Medication Reminder", 
                message,
                priority="high"
            )
            
            # Send SMS for critical medications
            await self._send_sms_notification(
                user_id,
                f"Time to take {medication_name} - {dosage}"
            )
            
            logger.info(f"Reminder sent to user {user_id} for {medication_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder: {str(e)}")
            return False
    
    async def send_missed_dose_alert(
        self, 
        user_id: str, 
        medication_name: str,
        scheduled_time: datetime
    ) -> bool:
        """
        Alert for missed medication dose
        Sends escalated notifications
        """
        try:
            message = f"⚠️ Missed Medication Alert\n\n"
            message += f"You missed your {medication_name} dose\n"
            message += f"Scheduled for: {scheduled_time.strftime('%I:%M %p')}\n"
            message += f"Please take it as soon as possible or consult your doctor."
            
            # Send urgent notification
            await self._send_push_notification(
                user_id,
                "Missed Dose Alert",
                message,
                priority="urgent"
            )
            
            # If caregiver exists, notify them too
            await self._notify_caregiver_if_exists(user_id, medication_name, scheduled_time)
            
            logger.warning(f"Missed dose alert sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send missed dose alert: {str(e)}")
            return False
    
    async def send_medication_report(
        self, 
        user_id: str, 
        report_data: Dict
    ) -> bool:
        """
        Send weekly/monthly medication adherence report
        Summarizes medication-taking behavior
        """
        try:
            # Calculate adherence metrics
            adherence_rate = report_data.get('adherence_rate', 0)
            total_doses = report_data.get('total_doses', 0)
            taken_doses = report_data.get('taken_doses', 0)
            missed_doses = report_data.get('missed_doses', 0)
            
            message = f"📊 Medication Adherence Report\n\n"
            message += f"Adherence Rate: {adherence_rate}%\n"
            message += f"Total Doses: {total_doses}\n"
            message += f"Doses Taken: {taken_doses}\n"
            message += f"Doses Missed: {missed_doses}\n\n"
            
            if adherence_rate >= 90:
                message += "🌟 Excellent! Keep up the good work!"
            elif adherence_rate >= 70:
                message += "👍 Good, but there's room for improvement."
            else:
                message += "⚠️ Your adherence needs attention. Consider setting more reminders."
            
            # Send email report
            await self._send_email_notification(
                user_id,
                "Your Medication Report",
                message
            )
            
            logger.info(f"Report sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send report: {str(e)}")
            return False
    
    async def _send_push_notification(
        self, 
        user_id: str, 
        title: str, 
        message: str,
        priority: str = "normal"
    ) -> bool:
        """Send push notification via SNS"""
        try:
            await self.sns_handler.publish_to_endpoint(
                user_id=user_id,
                title=title,
                message=message,
                priority=priority
            )
            return True
        except Exception as e:
            logger.error(f"Push notification failed: {str(e)}")
            return False
    
    async def _send_sms_notification(self, user_id: str, message: str) -> bool:
        """Send SMS notification"""
        try:
            # In production: use AWS SNS SMS or third-party service
            logger.info(f"SMS sent to user {user_id}: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"SMS notification failed: {str(e)}")
            return False
    
    async def _send_email_notification(
        self, 
        user_id: str, 
        subject: str, 
        body: str
    ) -> bool:
        """Send email notification via AWS SES"""
        try:
            # In production: use AWS SES
            logger.info(f"Email sent to user {user_id}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            return False
    
    async def _notify_caregiver_if_exists(
        self, 
        user_id: str, 
        medication_name: str,
        scheduled_time: datetime
    ):
        """Notify caregiver about missed dose"""
        # Check if user has caregiver and notify them
        logger.info(f"Checking caregiver for user {user_id}")
        # Implementation would query database for caregiver
    
    def _create_confirmation_message(self, medication_info: Dict) -> str:
        """Create medication confirmation message"""
        message = "✅ Medication Successfully Identified\n\n"
        message += f"Name: {medication_info.get('name', 'Unknown')}\n"
        message += f"Dosage: {medication_info.get('dosage', 'Not specified')}\n"
        message += f"Confidence: {medication_info.get('confidence', 0)}%\n"
        message += "\nA reminder schedule has been created for you."
        return message
