from typing import List
from backend.infrastructure.local_storage import get_calendar_path, get_email
from backend.models.patient import EmailCheckup
from backend.services.agents import EmailCreatorAgent, FrequencyDeciderAgent
import backend.services.emailscheduler as emailscheduler
import os
import schedule
import smtplib
import time
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from threading import Event, Thread

load_dotenv()

def send_email_smtp(sender_email, sender_password, recipient_email, email, attachment_path=None):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = email.subject

    msg.attach(MIMEText(email.body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def create_send_email_smtp(sender_email, sender_password, patient_id):

    # email preparation
    rf_email = EmailCreatorAgent(patient_id).compose_email_of_riskfactors(patient_id)
    p_email = None
    calendar_path = get_calendar_path(patient_id)
    recipienet_email = get_email(patient_id)
    if calendar_path:
        p_email = EmailCreatorAgent(patient_id).compose_email_of_prescription(patient_id)
        os.remove(calendar_path)
    
    #email sending
    send_email_smtp(sender_email, sender_password, recipienet_email, rf_email)
    send_email_smtp(sender_email, sender_password, recipienet_email, p_email, calendar_path)



def schedule_email(frequency, sender_email, sender_password, patient_id):
    if frequency == 'daily':
        job = schedule.every().day.at("09:00").do(create_send_email_smtp, sender_email, sender_password, patient_id)
    elif frequency == 'yearly':
        job = schedule.every().year.at("09:00").do(create_send_email_smtp, sender_email, sender_password, patient_id)
    elif frequency == 'weekly':
        job = schedule.every().week.at("09:00").do(create_send_email_smtp, sender_email, sender_password, patient_id)
    elif frequency == 'monthly':
        job = schedule.every(30).days.at("09:00").do(create_send_email_smtp, sender_email, sender_password, patient_id)
    else:
        job = None
    return job

def run_scheduler(stop_event):
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def get_all_email_checkups() -> List[EmailCheckup]:
    # This function should return a list of all EmailCheckup objects from the database
    # For demonstration purposes, we'll return an empty list
    return []

def check_and_update_schedules(email_checkups: List[EmailCheckup], sender_email, sender_password):
    for email_checkup in email_checkups:
        patient_id = email_checkup.patient_id
        new_frequency = FrequencyDeciderAgent(patient_id).decide_frequency()
        if new_frequency != email_checkup.frequency:
            schedule.cancel_job(email_checkup.job)
            email_checkup.frequency = new_frequency
            email_checkup.job = schedule_email(new_frequency, sender_email, sender_password, patient_id)

sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')

# Event to stop the scheduler thread
stop_event = Event()

# Start the scheduler in a separate thread
scheduler_thread = Thread(target=run_scheduler, args=(stop_event,))
scheduler_thread.start()

# Retrieve all EmailCheckup objects and schedule their email tasks
email_checkups = get_all_email_checkups()
for email_checkup in email_checkups:
    patient_id = email_checkup.patient_id
    frequency = email_checkup.frequency
    job = schedule_email(frequency, sender_email, sender_password, patient_id)
    email_checkup.job = job

# Periodically check for frequency changes every other day
try:
    while True:
        check_and_update_schedules(email_checkups, sender_email, sender_password)
        time.sleep(2 * 24 * 60 * 60)  # Sleep for 2 days
except KeyboardInterrupt:
    stop_event.set()
    scheduler_thread.join()