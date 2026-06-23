"""
Medication Scheduler Module
Automated scheduling and management of medication regimens
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from src.models.medication_model import Medication, MedicationSchedule, MedicationFrequency
from src.services.notification_service import NotificationService
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.exceptions import MedicationNotFoundError

class MedicationScheduler:
    """
    Automated medication scheduler
    Creates and manages medication schedules with reminders
    Integrates with AWS EventBridge for serverless scheduling
    """
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.notification_service = NotificationService()
        self.active_schedules: Dict[str, MedicationSchedule] = {}
        
        # Start scheduler
        self.scheduler.start()
        logger.info("Medication scheduler initialized")
    
    async def create_schedule(
        self, 
        user_id: str, 
        medication_info: Any
    ) -> MedicationSchedule:
        """
        Create automated medication schedule
        Generates reminder times based on frequency
        """
        try:
            # Determine schedule parameters
            frequency = self._determine_frequency(medication_info)
            duration_days = self._determine_duration(medication_info)
            reminder_times = self._calculate_reminder_times(frequency)
            
            # Create schedule object
            schedule = MedicationSchedule(
                medication_id=getattr(medication_info, 'id', 'unknown'),
                user_id=user_id,
                frequency=frequency,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration_days),
                reminder_times=reminder_times,
                reminders_enabled=True
            )
            
            # Store schedule
            self.active_schedules[schedule.id] = schedule
            
            # Schedule reminders
            await self._schedule_reminders(schedule)
            
            logger.info(f"Schedule created for user {user_id}: {frequency}")
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to create schedule: {str(e)}")
            raise
    
    async def update_schedule(
        self, 
        schedule_id: str, 
        updates: Dict[str, Any]
    ) -> MedicationSchedule:
        """
        Update existing medication schedule
        Modify frequency, times, or disable reminders
        """
        try:
            schedule = self.active_schedules.get(schedule_id)
            if not schedule:
                raise MedicationNotFoundError(f"Schedule {schedule_id} not found")
            
            # Remove old reminders
            await self._remove_reminders(schedule)
            
            # Update schedule fields
            for key, value in updates.items():
                if hasattr(schedule, key):
                    setattr(schedule, key, value)
            
            # Reschedule with new parameters
            await self._schedule_reminders(schedule)
            
            logger.info(f"Schedule {schedule_id} updated")
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to update schedule: {str(e)}")
            raise
    
    async def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel and remove medication schedule
        """
        try:
            schedule = self.active_schedules.pop(schedule_id, None)
            if schedule:
                await self._remove_reminders(schedule)
                logger.info(f"Schedule {schedule_id} cancelled")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel schedule: {str(e)}")
            return False
    
    async def get_user_schedules(self, user_id: str) -> List[MedicationSchedule]:
        """
        Get all active schedules for a user
        """
        return [
            schedule for schedule in self.active_schedules.values()
            if schedule.user_id == user_id
        ]
    
    async def get_upcoming_doses(self, user_id: str, hours: int = 24) -> List[Dict]:
        """
        Get upcoming medication doses for next hours
        """
        upcoming = []
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        
        for schedule in self.get_user_schedules(user_id):
            for reminder_time in schedule.reminder_times:
                # Parse reminder time
                hour, minute = map(int, reminder_time.split(':'))
                reminder_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if now <= reminder_datetime <= end_time:
                    upcoming.append({
                        "schedule_id": schedule.id,
                        "medication_id": schedule.medication_id,
                        "time": reminder_datetime.isoformat(),
                        "formatted_time": reminder_datetime.strftime("%I:%M %p")
                    })
        
        return sorted(upcoming, key=lambda x: x['time'])
    
    async def log_medication_taken(
        self, 
        schedule_id: str, 
        taken: bool = True
    ) -> Dict:
        """
        Log medication as taken or missed
        Updates adherence tracking
        """
        try:
            schedule = self.active_schedules.get(schedule_id)
            if not schedule:
                raise MedicationNotFoundError(f"Schedule {schedule_id} not found")
            
            # Update adherence metrics
            if taken:
                schedule.adherence_rate = min(100, schedule.adherence_rate + 5)
            else:
                schedule.adherence_rate = max(0, schedule.adherence_rate - 2)
                # Send missed dose alert
                await self.notification_service.send_missed_dose_alert(
                    schedule.user_id,
                    schedule.medication_id,
                    datetime.now()
                )
            
            logger.info(f"Medication logged for schedule {schedule_id}: taken={taken}")
            
            return {
                "schedule_id": schedule_id,
                "taken": taken,
                "adherence_rate": schedule.adherence_rate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to log medication: {str(e)}")
