# Healthcare Agent

## Problem Statement

Hospitals struggle to provide timely, personalized care to patients due to overburdened staff and inefficient follow-up systems. This leads to missed appointments, delayed interventions, and poor patient outcomes. An AI-powered remote care agent is needed to automate patient engagement, analyze health data, and proactively coordinate care—reducing costs, improving outcomes, and enhancing patient satisfaction.

This is a healthcare agent application built with FastAPI. The application provides various endpoints for managing lab reports, prescriptions, conversations, and sending emails. It also integrates with Twilio SendGrid for sending emails.


## Features

### 1. Update Patients' Calendar Based on Prescriptions

When a new prescription is added for a patient, the application updates the patient's calendar with the prescription details. This helps patients keep track of their medication schedules and ensures they follow their prescribed treatments.

### 2. Deduce Risk Factors

The application deduces risk factors for patients based on their lab reports, recent activities, and conversations with the agent. This helps in identifying potential health risks and taking preventive measures.

### 3. Compose and Send Personalized Emails

The application composes and sends personalized emails to users based on their risk factors. The emails include awareness about the identified risks and suggestions for mitigating them. This feature uses Twilio SendGrid for sending emails.

### 4. Provide Explanations and Action Suggestions for Nurses

The application provides detailed explanations and suggested actions for nurses based on lab reports. This helps nurses understand the lab results better and take appropriate actions for patient care.

### 5. Talk to Patients About Their Health Status

The application engages in conversations with patients about their health status and general health knowledge. This helps in educating patients and keeping them informed about their health conditions.

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- Streamlit
- Python-dotenv
- Twilio
- SendGrid

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
pip install -r [requirements.txt](http://_vscodecontentref_/0)
```
5. Set up .env
   Create a .env file in the root directory and add the following environment variables:
```sh
# .env
SENDGRID_API_KEY=your_sendgrid_api_key_here
GEMINI_LLM_API_URL=https://api.gemini-llm.com/analyze
GEMINI_LLM_API_KEY=your_gemini_llm_api_key_here
```
## Run the Application
To run the FastAPI application, use the following command:

```sh
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
License
This project is licensed under the MIT License. See the LICENSE file for details.
