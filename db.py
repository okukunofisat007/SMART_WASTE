
import os
import uuid
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client


# ==========================================
# SUPABASE CONNECTION
# ==========================================

@st.cache_resource
def get_connection():
    config = st.secrets["supabase"]

    return create_client(
        config["url"],
        config["secret_key"]
    )


def test_connection():
    try:
        supabase = get_connection()

        response = (
            supabase.table("waste_categories")
            .select("category_id")
            .limit(1)
            .execute()
        )

        return True, "Supabase connection successful."

    except Exception as error:
        return False, str(error)


# ==========================================
# IMAGE UPLOAD
# ==========================================

def upload_waste_image(
    uploaded_file,
    user_id,
    file_name=None,
    content_type=None
):
    if not user_id:
        raise ValueError("User ID is required.")

    if uploaded_file is None:
        raise ValueError("Please provide an image.")

    if isinstance(uploaded_file, (bytes, bytearray)):
        file_bytes = bytes(uploaded_file)
    else:
        file_bytes = uploaded_file.getvalue()

    if not file_bytes:
        raise ValueError("The image is empty.")

    original_name = (
        file_name
        or getattr(uploaded_file, "name", "waste_image.jpg")
    )

    extension = os.path.splitext(original_name)[1].lower()

    if not extension:
        extension = ".jpg"

    content_type = (
        content_type
        or getattr(uploaded_file, "type", None)
        or "image/jpeg"
    )

    file_path = f"{user_id}/{uuid.uuid4()}{extension}"

    supabase = get_connection()

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
# WASTE REPORTS
# ==========================================

def save_waste_report(
    area,
    problem_type,
    description,
    latitude=None,
    longitude=None,
    accuracy=None,
    image_bytes=None,
    image_content_type="image/jpeg",
    user_id=None,
    image_path=None
):
    if not user_id:
        raise ValueError("Please log in before submitting a report.")

    if not area or not area.strip():
        raise ValueError("Area is required.")

    if not problem_type:
        raise ValueError("Waste problem type is required.")

    supabase = get_connection()

    if image_bytes is not None:
        image_path = upload_waste_image(
            uploaded_file=image_bytes,
            user_id=user_id,
            content_type=image_content_type
        )

    captured_at = (
        datetime.now(timezone.utc).isoformat()
        if latitude is not None and longitude is not None
        else None
    )

    report_data = {
        "report_type": "General Waste",
        "area": area.strip(),
        "problem_type": problem_type,
        "description": description,
        "latitude": latitude,
        "longitude": longitude,
        "location_accuracy_m": accuracy,
        "location_captured_at": captured_at,
        "image_path": image_path,
        "status": "Pending",
        "user_id": user_id
    }

    response = (
        supabase.table("waste_reports")
        .insert(report_data)
        .execute()
    )

    if not response.data:
        raise Exception("Waste report could not be saved.")

    return response.data[0]["report_id"]


def get_all_reports():
    supabase = get_connection()

    response = (
        supabase.table("waste_reports")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    return pd.DataFrame(response.data or [])


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


def get_user_report_stats(user_id):
    if not user_id:
        return {
            "total_reports": 0,
            "pending_reports": 0,
            "in_progress_reports": 0,
            "resolved_reports": 0
        }

    reports = get_user_reports(user_id)

    if reports.empty:
        statuses = []
    else:
        statuses = (
            reports["status"]
            .fillna("")
            .str.lower()
            .tolist()
        )

    return {
        "total_reports": len(statuses),
        "pending_reports": statuses.count("pending"),
        "in_progress_reports": statuses.count("in progress"),
        "resolved_reports": statuses.count("resolved")
    }


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
# WASTE CATEGORIES
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
# RESIDENT LOCATIONS
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

    return response.data[0] if response.data else None


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
        raise ValueError("Community or area is required.")

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
        "location_accuracy_m": accuracy,
        "captured_at": now,
        "updated_at": now
    }

    response = (
        supabase.table("resident_locations")
        .upsert(
            location_data,
            on_conflict="user_id"
        )
        .execute()
    )

    if not response.data:
        raise Exception("Resident location could not be saved.")

    return response.data[0]


# ==========================================
# AI WASTE CLASSIFICATION
# ==========================================

def save_waste_classification(
    user_id,
    category_name,
    image_path,
    confidence_score,
    model_version="MobileNetV3-Small",
    report_id=None
):
    if not user_id:
        raise ValueError("User ID is required.")

    if not image_path:
        raise ValueError("Image path is required.")

    if not category_name:
        raise ValueError("Waste category is required.")

    supabase = get_connection()

    category_response = (
        supabase.table("waste_categories")
        .select("category_id")
        .ilike("category_name", category_name.strip())
        .eq("is_active", True)
        .limit(1)
        .execute()
    )

    if not category_response.data:
        raise ValueError(
            f"Category '{category_name}' does not exist "
            "or is inactive in the database."
        )

    classification_data = {
        "user_id": user_id,
        "category_id": category_response.data[0]["category_id"],
        "image_path": image_path,
        "confidence_score": float(confidence_score),
        "model_version": model_version
    }

    if report_id is not None:
        classification_data["report_id"] = report_id

    response = (
        supabase.table("waste_classifications")
        .insert(classification_data)
        .execute()
    )

    if not response.data:
        raise Exception("Waste classification could not be saved.")

    return response.data[0]["classification_id"]


# ==========================================
# WASTE2EARN SUBMISSIONS
# ==========================================

def save_recycling_submission(
    user_id,
    classification_id,
    quantity,
    quantity_unit
):
    if not user_id:
        raise ValueError("User ID is required.")

    if not classification_id:
        raise ValueError("Classification ID is required.")

    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError("Quantity must be a whole number.")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")

    allowed_units = ["Pieces", "kg", "Bags"]

    if quantity_unit not in allowed_units:
        raise ValueError(
            "Unit must be Pieces, kg or Bags."
        )

    supabase = get_connection()

    location = get_resident_location(user_id)

    if not location:
        raise ValueError(
            "Please save your residential location before submitting."
        )

    submission_data = {
        "user_id": user_id,
        "classification_id": classification_id,
        "location_id": location["location_id"],
        "pickup_address": location["residential_address"],
        "pickup_area": location["area"],
        "pickup_latitude": location["latitude"],
        "pickup_longitude": location["longitude"],
        "quantity": quantity,
        "quantity_unit": quantity_unit,
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
# RECYCLING STATISTICS
# ==========================================

def get_user_recycling_stats(user_id):
    if not user_id:
        return {
            "total_points": 0,
            "total_quantity": 0,
            "total_submissions": 0,
            "quantity_by_unit": {}
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

    quantity_by_unit = {}

    total_points = 0
    total_quantity = 0

    for submission in submissions:
        unit = submission.get("quantity_unit") or "Unknown"
        quantity = submission.get("quantity") or 0

        quantity_by_unit[unit] = (
            quantity_by_unit.get(unit, 0) + quantity
        )

        total_quantity += quantity
        total_points += submission.get("awarded_points") or 0

    return {
        "total_points": total_points,
        "total_quantity": total_quantity,
        "total_submissions": len(submissions),
        "quantity_by_unit": quantity_by_unit
    }
