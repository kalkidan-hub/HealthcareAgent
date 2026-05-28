import streamlit as st
import requests

BASE_API = "http://localhost:8000"


def _auth_headers():
    token = st.session_state.get("auth_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def _store_auth(payload: dict):
    st.session_state.auth_token = payload["access_token"]
    st.session_state.current_user = payload["user"]


def patient_dashboard():
    st.title("Healthcare Portal")

    if "auth_token" not in st.session_state:
        mode = st.radio("Access", ["Login", "Register"], horizontal=True)

        with st.form("auth_form"):
            name = st.text_input("Name") if mode == "Register" else ""
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["patient", "doctor"]) if mode == "Register" else "patient"
            age = st.number_input("Age", min_value=0, step=1) if mode == "Register" else 0
            submitted = st.form_submit_button(mode)

        if submitted:
            payload = {"email": email, "password": password}
            endpoint = "/api/auth/login"
            if mode == "Register":
                payload.update({"name": name, "role": role, "age": int(age)})
                endpoint = "/api/auth/register"

            response = requests.post(f"{BASE_API}{endpoint}", json=payload, timeout=20)
            if response.ok:
                _store_auth(response.json())
                st.rerun()
            else:
                detail = response.json().get("detail", "Authentication failed")
                st.error(detail)
        return

    response = requests.get(f"{BASE_API}/api/auth/me", headers=_auth_headers(), timeout=20)
    if not response.ok:
        st.session_state.pop("auth_token", None)
        st.session_state.pop("current_user", None)
        st.error("Session expired. Please sign in again.")
        st.rerun()
        return

    current_user = response.json()
    st.success(f"Signed in as {current_user['name']} ({current_user['role']})")
    st.write(f"User ID: {current_user['id']}")

    if st.button("Logout"):
        st.session_state.pop("auth_token", None)
        st.session_state.pop("current_user", None)
        st.rerun()