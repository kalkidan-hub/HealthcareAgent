import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
import schedule
import time
from threading import Thread, Event

load_dotenv()

def send_email_smtp(sender_email, sender_password, recipient_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        print("Logging in...")
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        print("Email sent successfully")
    except Exception as e:
        print(f"Failed to send email: {e}")

def schedule_email(frequency, sender_email, sender_password, recipient_email, subject, body):
    if frequency == 'daily':
        job = schedule.every().day.at("09:00").do(send_email_smtp, sender_email, sender_password, recipient_email, subject, body)
    elif frequency == 'hourly':
        job = schedule.every().hour.do(send_email_smtp, sender_email, sender_password, recipient_email, subject, body)
    elif frequency == 'minute':
        job = schedule.every().minute.do(send_email_smtp, sender_email, sender_password, recipient_email, subject, body)
    else:
        print("Unsupported frequency")
        job = None
    return job

def run_scheduler(stop_event):
    while not stop_event.is_set():
        schedule.run_pending()
        time.sleep(1)

def freq_changer(current_freq):
    if current_freq == 'daily':
        return 'hourly'
    elif current_freq == 'hourly':
        return 'minute'
    else:
        return 'daily'

# Example usage
sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')
recipient_email = 'kalkidandereje666@gmail.com'
subject = 'Subject'
body = 'Email body'
frequency = 'minute'

# Event to stop the scheduler thread
stop_event = Event()

# Start the scheduler in a separate thread
scheduler_thread = Thread(target=run_scheduler, args=(stop_event,))
scheduler_thread.start()

# Schedule the email to be sent at the initial frequency
current_job = schedule_email(frequency, sender_email, sender_password, recipient_email, subject, body)

# Periodically check for frequency changes
try:
    while True:
        new_frequency = freq_changer(frequency)
        if new_frequency != frequency:
            if current_job:
                schedule.cancel_job(current_job)  # Cancel the current job
            frequency = new_frequency
            current_job = schedule_email(frequency, sender_email, sender_password, recipient_email, subject, body)
        time.sleep(10)  # Check for changes every 10 seconds
except KeyboardInterrupt:
    stop_event.set()
    scheduler_thread.join()