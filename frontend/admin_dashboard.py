import streamlit as st
import requests

BASE_API = "http://localhost:8000"

def patient_dashboard():
    st.title("Patient Portal")
    
    if 'patient_id' not in st.session_state:
        patient_id = st.text_input("Enter Patient ID")
        if patient_id:
            st.session_state.patient_id = patient_id
            
    if 'patient_id' in st.session_state:
        st.write(f"Welcome Patient {st.session_state.patient_id}")
        
        # Display alerts
        alerts = requests.get(f"{BASE_API}/check-patient/{st.session_state.patient_id}")
        if alerts.json().get('alerts'):
            st.error("ALERTS: " + ", ".join(alerts.json()['alerts']))