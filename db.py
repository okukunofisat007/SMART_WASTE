import streamlit as st
import mysql.connector
from supabase import create_client

def get_connection():
    config = st.secrets["mysql"]

    connection = mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"]
    )

    return connection


def test_connection():
    try:
        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE()")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return True, result[0]

    except Exception as e:
        return False, str(e)




def save_waste_report(
    area,
    problem_type,
    description,
    latitude=None,
    longitude=None,
    accuracy=None,
    image_bytes=None,
    image_content_type="image/jpeg",
    quantity=None,
    quantity_unit=None
):

    import uuid
    from datetime import datetime, timezone

    config = st.secrets["supabase"]

    supabase = create_client(
        config["url"],
        config["key"]
    )

    image_path = None

    # UPLOAD IMAGE TO SUPABASE STORAGE
    if image_bytes is not None:

        extension = (
            "png" if image_content_type == "image/png"
            else "jpg"
        )

        image_path = f"waste_reports/{uuid.uuid4()}.{extension}"

        supabase.storage.from_("waste-images").upload(
            image_path,
            image_bytes,
            file_options={
                "content-type": image_content_type
            }
        )

    captured_at = (
        datetime.now(timezone.utc).isoformat()
        if latitude is not None and longitude is not None
        else None
    )

    report_data = {
        "report_type": "General Waste",
        "area": area,
        "problem_type": problem_type,
        "description": description,
        "latitude": latitude,
        "longitude": longitude,
        "location_accuracy_m": accuracy,
        "location_captured_at": captured_at,
        "image_path": image_path,
        "quantity": quantity,
        "quantity_unit": quantity_unit,
        "status": "Pending"
    }

    response = (
        supabase
        .table("waste_reports")
        .insert(report_data)
        .execute()
    )

    return response.data[0]["report_id"]


def get_all_reports():

    import pandas as pd

    config = st.secrets["supabase"]

    supabase = create_client(
        config["url"],
        config["key"]
    )

    response = (
        supabase
        .table("waste_reports")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    df = pd.DataFrame(response.data)

    return df

# function that retrieves report that have GPS coordinates

def get_map_reports():

    import pandas as pd

    config = st.secrets["supabase"]

    supabase = create_client(
        config["url"],
        config["key"]
    )

    response = (
        supabase
        .table("waste_reports")
        .select(
            "report_id, area, problem_type, description, latitude, longitude, status"
        )
        .not_.is_("latitude", "null")
        .not_.is_("longitude", "null")
        .execute()
    )

    df = pd.DataFrame(response.data)

    return df
