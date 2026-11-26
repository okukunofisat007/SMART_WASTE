
import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timezone
import uuid
import os

# ==========================================
# SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def get_connection():
    """Server-side Supabase client."""

    config = st.secrets["supabase"]

    return create_client(
        config["url"],
        config["secret_key"]
    )

@st.cache_resource
def get_public_connection():
    """Public Supabase client for authentication."""

    config = st.secrets["supabase"]

    return create_client(
        config["url"],
        config["publishable_key"]
    )

# ==========================================
# TEST DATABASE CONNECTION
# ==========================================

def test_connection():

    try:
        supabase = get_connection()

        response = (
            supabase.table("waste_categories")
            .select("category_id")
            .limit(1)
            .execute()
        )

        return response.data is not None

    except Exception as e:
        print(f"Database connection error: {e}")
        return False

# ==========================================
# SAVE WASTE REPORT
# ==========================================

def save_waste_report(
    area,
    problem_type=None,
    description=None,
    latitude=None,
    longitude=None,
    accuracy=None,
    user_id=None,
    image_path=None,
    waste_type=None
):

    if not area:
        raise ValueError("Area is required.")

    report_problem = problem_type or waste_type

    if not report_problem:
        raise ValueError("Waste problem type is required.")

    if not user_id:
        raise ValueError("User ID is required.")

    supabase = get_connection()

    report_data = {
        "report_type": "General Waste",
        "area": area,
        "problem_type": report_problem,
        "description": description,
        "latitude": latitude,
        "longitude": longitude,
        "location_accuracy_m": accuracy,
        "location_captured_at": (
            datetime.now(timezone.utc).isoformat()
            if latitude is not None and longitude is not None
            else None
        ),
        "status": "Pending",
        "user_id": user_id,
        "image_path": image_path
    }

    response = (
        supabase.table("waste_reports")
        .insert(report_data)
        .execute()
    )

    if not response.data:
        raise Exception("Waste report could not be saved.")

    return response.data[0]["report_id"]

# ==========================================
# GET ALL WASTE REPORTS
# ==========================================

def get_all_reports():

    supabase = get_connection()

    response = (
        supabase.table("waste_reports")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(response.data or [])

# ==========================================
# GET USER WASTE REPORTS
# ==========================================

def get_user_reports(user_id):

    if not user_id:
        return pd.DataFrame()

    supabase = get_connection()

    response = (
        supabase.table("waste_reports")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(response.data or [])

# ==========================================
# GET USER REPORT STATISTICS
# ==========================================

def get_user_report_stats(user_id):

    if not user_id:
        return {
            "total_reports": 0,
            "pending_reports": 0,
            "in_progress_reports": 0,
            "resolved_reports": 0
        }

    supabase = get_connection()

    response = (
        supabase.table("waste_reports")
        .select("report_id, status")
        .eq("user_id", user_id)
        .execute()
    )

    reports = response.data or []

    pending = 0
    in_progress = 0
    resolved = 0

    for report in reports:

        status = str(
            report.get("status") or ""
        ).strip().lower()

        if status == "pending":
            pending += 1

        elif status == "in progress":
            in_progress += 1

        elif status == "resolved":
            resolved += 1

    return {
        "total_reports": len(reports),
        "pending_reports": pending,
        "in_progress_reports": in_progress,
        "resolved_reports": resolved
    }

# ==========================================
# GET USER RECYCLING STATISTICS
# ==========================================

def get_user_recycling_stats(user_id):

    if not user_id:
        return {
            "total_points": 0,
            "total_bottles": 0,
            "total_submissions": 0
        }

    supabase = get_connection()

    response = (
        supabase.table("recycling_submissions")
        .select(
            "submission_id, quantity, quantity_unit, awarded_points"
        )
        .eq("user_id", user_id)
        .execute()
    )

    submissions = response.data or []

    total_points = 0
    total_bottles = 0

    for submission in submissions:

        awarded_points = submission.get("awarded_points")

        if awarded_points is not None:
            total_points += int(awarded_points)

        if str(
            submission.get("quantity_unit") or ""
        ).lower() == "bottles":

            total_bottles += int(
                submission.get("quantity") or 0
            )

    return {
        "total_points": total_points,
        "total_bottles": total_bottles,
        "total_submissions": len(submissions)
    }

# ==========================================
# GET REPORTS FOR MAP
# ==========================================

def get_map_reports():

    supabase = get_connection()

    response = (
        supabase.table("waste_reports")
        .select(
            "report_id, area, problem_type, description, "
            "latitude, longitude, status, created_at"
        )
        .not_.is_("latitude", "null")
        .not_.is_("longitude", "null")
        .execute()
    )

    return pd.DataFrame(response.data or [])

# ==========================================
# GET ACTIVE WASTE CATEGORIES
# ==========================================

def get_waste_categories():

    supabase = get_connection()

    response = (
        supabase.table("waste_categories")
        .select(
            "category_id, category_name, "
            "is_recyclable, recycling_points"
        )
        .eq("is_active", True)
        .order("category_name")
        .execute()
    )

    return pd.DataFrame(response.data or [])

# ==========================================
# GET RESIDENT LOCATION
# ==========================================

def get_resident_location(user_id):

    if not user_id:
        return None

    supabase = get_connection()

    response = (
        supabase.table("resident_locations")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

# ==========================================
# SAVE OR UPDATE RESIDENT LOCATION
# ==========================================

def save_resident_location(
    user_id,
    residential_address,
    area,
    latitude,
    longitude,
    accuracy=None
):

    if not user_id:
        raise ValueError("User ID is required.")

    if not residential_address or not residential_address.strip():
        raise ValueError("Residential address is required.")

    if not area or not area.strip():
        raise ValueError("Residential area is required.")

    if latitude is None or longitude is None:
        raise ValueError("GPS coordinates are required.")

    supabase = get_connection()

    now = datetime.now(timezone.utc).isoformat()

    location_data = {
        "user_id": user_id,
        "residential_address": residential_address.strip(),
        "area": area.strip(),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "location_accuracy_m": (
            float(accuracy) if accuracy is not None else None
        ),
        "captured_at": now,
        "updated_at": now
    }

    existing_location = get_resident_location(user_id)

    if existing_location:

        response = (
            supabase.table("resident_locations")
            .update(location_data)
            .eq(
                "location_id",
                existing_location["location_id"]
            )
            .execute()
        )

    else:

        response = (
            supabase.table("resident_locations")
            .insert(location_data)
            .execute()
        )

    if not response.data:
        raise Exception("Residential location could not be saved.")

    return response.data[0]

# ==========================================
# UPLOAD WASTE IMAGE
# ==========================================

def upload_waste_image(
    uploaded_file,
    user_id,
    file_name=None
):

    if uploaded_file is None:
        raise ValueError("No image was provided.")

    if not user_id:
        raise ValueError("User ID is required.")

    supabase = get_connection()

    original_name = file_name or getattr(
        uploaded_file,
        "name",
        "waste_image.jpg"
    )

    extension = os.path.splitext(original_name)[1] or ".jpg"

    unique_name = f"{uuid.uuid4()}{extension}"

    file_path = f"{user_id}/{unique_name}"

    if isinstance(uploaded_file, bytes):
        file_bytes = uploaded_file

    elif isinstance(uploaded_file, bytearray):
        file_bytes = bytes(uploaded_file)

    elif hasattr(uploaded_file, "getvalue"):
        file_bytes = uploaded_file.getvalue()

    else:
        raise ValueError("Unsupported image format.")

    content_type = getattr(
        uploaded_file,
        "type",
        "image/jpeg"
    )

    supabase.storage.from_("waste-images").upload(
        path=file_path,
        file=file_bytes,
        file_options={
            "content-type": content_type,
            "upsert": "false"
        }
    )

    return file_path

# ==========================================
# SAVE AI WASTE CLASSIFICATION
# ==========================================

def save_waste_classification(
    user_id,
    category_name,
    image_path,
    confidence_score,
    model_version="MobileNetV3-Small"
):

    if not user_id:
        raise ValueError("User ID is required.")

    if not category_name:
        raise ValueError("Waste category is required.")

    if not image_path:
        raise ValueError("Image path is required.")

    supabase = get_connection()

    category_response = (
        supabase.table("waste_categories")
        .select("category_id, category_name")
        .eq("category_name", category_name)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not category_response.data:
        raise ValueError(
            f"Active waste category '{category_name}' was not found."
        )

    category_id = category_response.data[0]["category_id"]

    classification_data = {
        "user_id": user_id,
        "category_id": category_id,
        "image_path": image_path,
        "confidence_score": float(confidence_score),
        "model_version": model_version
    }

    response = (
        supabase.table("waste_classifications")
        .insert(classification_data)
        .execute()
    )

    if not response.data:
        raise Exception("Waste classification could not be saved.")

    return response.data[0]["classification_id"]

# ==========================================
# SAVE RECYCLING SUBMISSION
# ==========================================

def save_recycling_submission(
    user_id,
    classification_id,
    number_of_bottles
):

    if not user_id:
        raise ValueError("User ID is required.")

    if not classification_id:
        raise ValueError("Classification ID is required.")

    if number_of_bottles is None or int(number_of_bottles) < 1:
        raise ValueError("Enter at least one bottle.")

    supabase = get_connection()

    resident_location = get_resident_location(user_id)

    if not resident_location:
        raise ValueError(
            "No residential location found. "
            "Please save your location first."
        )

    submission_data = {
        "user_id": user_id,
        "classification_id": classification_id,
        "location_id": resident_location["location_id"],
        "pickup_address": resident_location["residential_address"],
        "pickup_area": resident_location["area"],
        "pickup_latitude": resident_location["latitude"],
        "pickup_longitude": resident_location["longitude"],
        "quantity": int(number_of_bottles),
        "quantity_unit": "bottles",
        "estimated_points": None,
        "awarded_points": None,
        "status": "pending",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }

    response = (
        supabase.table("recycling_submissions")
        .insert(submission_data)
        .execute()
    )

    if not response.data:
        raise Exception("Recycling submission could not be saved.")

    return response.data[0]["submission_id"]

# ==========================================
# CREATE USER ACCOUNT
# ==========================================

def create_user(
    full_name,
    email,
    password,
    role="user",
    phone=None
):

    if role != "user":
        raise ValueError(
            "Only user accounts can be registered here."
        )

    if not full_name or not email or not password:
        raise ValueError(
            "Full name, email and password are required."
        )

    admin_client = get_connection()

    auth_response = admin_client.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True
    })

    auth_user = auth_response.user

    if not auth_user:
        raise Exception("User account could not be created.")

    user_id = auth_user.id

    profile_data = {
        "user_id": user_id,
        "full_name": full_name,
        "email": email,
        "role": role,
        "phone": phone,
        "is_active": True
    }

    try:

        response = (
            admin_client.table("users")
            .insert(profile_data)
            .execute()
        )

        if not response.data:
            raise Exception("User profile could not be created.")

        return response.data[0]

    except Exception:

        admin_client.auth.admin.delete_user(user_id)

        raise

# ==========================================
# VERIFY USER LOGIN
# ==========================================

def verify_user(email, password):

    public_client = get_public_connection()

    auth_response = public_client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

    if not auth_response.user:
        return None

    user_id = auth_response.user.id

    admin_client = get_connection()

    profile_response = (
        admin_client.table("users")
        .select("*")
        .eq("user_id", user_id)
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not profile_response.data:
        return None

    return profile_response.data[0]