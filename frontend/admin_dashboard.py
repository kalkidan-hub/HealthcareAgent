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


def _clean_optional_text(value: str) -> str | None:
    value = (value or "").strip()
    return value or None


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
            sex = st.text_input("Sex") if mode == "Register" else ""
            contact_number = st.text_input("Contact number") if mode == "Register" else ""
            emergency_number = st.text_input("Emergency number") if mode == "Register" else ""
            submitted = st.form_submit_button(mode)

        if submitted:
            payload = {"email": email, "password": password}
            endpoint = "/api/auth/login"
            if mode == "Register":
                payload.update(
                    {
                        "name": name,
                        "role": role,
                        "age": int(age),
                        "sex": _clean_optional_text(sex),
                        "contact_number": _clean_optional_text(contact_number),
                        "emergency_number": _clean_optional_text(emergency_number),
                    }
                )
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

    with st.expander("Edit profile", expanded=False):
        with st.form("profile_form"):
            name = st.text_input("Name", value=current_user.get("name", ""))
            email = st.text_input("Email", value=current_user.get("email", ""))
            age = st.number_input("Age", min_value=0, step=1, value=int(current_user.get("age") or 0))
            sex = st.text_input("Sex", value=current_user.get("sex") or "")
            contact_number = st.text_input("Contact number", value=current_user.get("contact_number") or "")
            emergency_number = st.text_input("Emergency number", value=current_user.get("emergency_number") or "")
            profile_submitted = st.form_submit_button("Save profile")

        if profile_submitted:
            payload = {
                "name": _clean_optional_text(name),
                "email": _clean_optional_text(email),
                "age": int(age),
                "sex": _clean_optional_text(sex),
                "contact_number": _clean_optional_text(contact_number),
                "emergency_number": _clean_optional_text(emergency_number),
            }
            response = requests.put(f"{BASE_API}/api/auth/me", headers=_auth_headers(), json=payload, timeout=20)
            if response.ok:
                updated_user = response.json()
                st.session_state.current_user = updated_user
                st.success("Profile updated")
                st.rerun()
            else:
                detail = response.json().get("detail", "Profile update failed")
                st.error(detail)

    if st.button("Logout"):
        st.session_state.pop("auth_token", None)
        st.session_state.pop("current_user", None)
        st.rerun()