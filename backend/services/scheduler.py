from google.cloud import scheduler_v1
from backend.infrastructure.gemini_llm import HealthcareLLM

class EngagementService:
    def __init__(self):
        self.scheduler = scheduler_v1.CloudSchedulerClient()
        self.llm = HealthcareLLM()
    
    def schedule_post_op_checkins(self, patient_id):
        messages = {
            1: "How is your pain level today? Reply 1-10",
            3: "Are you experiencing any redness or swelling?",
            7: "How's your recovery progressing?"
        }
        
        for day, message in messages.items():
            self._create_scheduler_job(
                patient_id,
                f"post-op-day-{day}",
                message,
                f"0 9 {day} * *"  # 9 AM on day X
            )
    
    def _create_scheduler_job(self, patient_id, job_id, message, schedule):
        job = {
            "name": f"projects/YOUR_PROJECT_ID/locations/us-central1/jobs/{job_id}-{patient_id}",
            "http_target": {
                "uri": f"https://yourapi.com/send-message/{patient_id}",
                "http_method": "POST",
                "body": message.encode('utf-8')
            },
            "schedule": schedule,
            "time_zone": "UTC"
        }
        self.scheduler.create_job(parent="projects/YOUR_PROJECT_ID/locations/us-central1", job=job)