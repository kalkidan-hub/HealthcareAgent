# Healthcare Agent

## Problem Statement

Hospitals struggle to provide timely, personalized care to patients due to overburdened staff and inefficient follow-up systems. This leads to missed appointments, delayed interventions, and poor patient outcomes. An AI-powered remote care agent is needed to automate patient engagement, analyze health data, and proactively coordinate care—reducing costs, improving outcomes, and enhancing patient satisfaction.

This is a healthcare agent application built with FastAPI. The application provides various endpoints for managing lab reports, prescriptions, conversations, and sending emails. It also integrates with Twilio SendGrid for sending emails.

## Features

1. **Agentic Dynamic Patient Check-Up via Email**:
   - Automatically schedules and sends emails to patients based on their health status and risk factors.

2. **Risk Factor Extraction and Remediation**:
   - Extracts risk factors from patient's records and sends emails to patients with information and remediation steps.

3. **Electronic Health Records (EHR) for Doctors**:
   - Provides doctors with comprehensive EHRs of patients, including risk factors and prescriptions.

## Upcoming Features

1. **Chatbot for Patients**:
   - A chatbot that allows patients to interact with the healthcare assistant about their health status and other health-related queries.

2. **Appointment Scheduling with Doctors**:
   - Enables patients to schedule appointments with doctors directly through the platform.

3. **Demographical Health Status Reporting**:
   - Analyzes and reports on the health status of different demographics based on patients' EHRs.


## Requirements



## Installation

1. Clone the repository:

```sh
git clone https://github.com/your-username/healthcare_agent.git
cd healthcare_agent
```
3. Create and activate Virtual environment
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
4. Install Dependenies
```sh
pip install -r requirements.txt
```
5. Set up .env
   Create a .env file in the root directory and add the following environment variables:
```sh
# .env
GOOGLE_APPLICATION_CREDENTIALS=...
GOOGLE_PROJECT_ID=...
SENDER_EMAIL = ...
SENDER_PASSWORD = ...
```
## Run the Application
To run the FastAPI application, use the following command:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
License
This project is licensed under the MIT License. See the LICENSE file for details.
