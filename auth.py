
from supabase import create_client
import streamlit as st


# ==========================================
# SUPABASE CLIENTS
# ==========================================

def get_public_client():
    """Client for normal user authentication."""

    config = st.secrets["supabase"]

    return create_client(
        config["url"],
        config["publishable_key"]
    )


def get_admin_client():
    """Server-side client for account administration."""

    config = st.secrets["supabase"]

    return create_client(
        config["url"],
        config["secret_key"]
    )


# ==========================================
# CREATE USER ACCOUNT
# ==========================================

def register_user(full_name, email, password, phone=None):

    supabase = get_admin_client()

    auth_response = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })

    auth_user = auth_response.user

    if auth_user is None:
        raise Exception("Could not create user account.")

    profile_data = {
        "user_id": str(auth_user.id),
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "role": "user",
        "is_active": True
    }

    try:

        supabase.table("users").insert(
            profile_data
        ).execute()

    except Exception:

        supabase.auth.admin.delete_user(
            auth_user.id
        )

        raise

    return str(auth_user.id)


# ==========================================
# CREATE ADMIN ACCOUNT
# ==========================================

def create_admin(full_name, email, password, phone=None):

    supabase = get_admin_client()

    auth_response = supabase.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })

    auth_user = auth_response.user

    if auth_user is None:
        raise Exception("Could not create administrator account.")

    profile_data = {
        "user_id": str(auth_user.id),
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "role": "admin",
        "is_active": True
    }

    try:

        supabase.table("users").insert(
            profile_data
        ).execute()

    except Exception:

        supabase.auth.admin.delete_user(
            auth_user.id
        )

        raise

    return str(auth_user.id)


# ==========================================
# LOGIN USER OR ADMIN
# ==========================================

def login_user(email, password):

    auth_client = get_public_client()

    try:

        response = auth_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        auth_user = response.user

        if auth_user is None:
            return None

        admin_client = get_admin_client()

        profile_response = (
            admin_client.table("users")
            .select("*")
            .eq("user_id", str(auth_user.id))
            .eq("is_active", True)
            .single()
            .execute()
        )

        profile = profile_response.data

        if not profile:
            auth_client.auth.sign_out()
            return None

        return {
            "user": profile,
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
        }

    except Exception:
        return None


# ==========================================
# LOGOUT
# ==========================================

def logout_user():

    for key in [
        "user",
        "access_token",
        "refresh_token",
        "authenticated"
    ]:

        st.session_state.pop(key, None)
