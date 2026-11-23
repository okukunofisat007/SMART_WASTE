import streamlit as st
import mysql.connector


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
    accuracy=None
):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO waste_reports (
                report_type,
                area,
                problem_type,
                description,
                latitude,
                longitude,
                location_accuracy_m,
                location_captured_at,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        from datetime import datetime

        captured_at = (
            datetime.now()
            if latitude is not None and longitude is not None
            else None
        )

        values = (
            "General Waste",
            area,
            problem_type,
            description,
            latitude,
            longitude,
            accuracy,
            captured_at,
            "Pending"
        )

        cursor.execute(query, values)
        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()

def get_all_reports():

    connection = get_connection()

    try:
        query = """
            SELECT *
            FROM waste_reports
            ORDER BY created_at DESC
        """

        import pandas as pd

        df = pd.read_sql(query, connection)

        return df

    finally:
        connection.close()

# function that retrieves report that have GPS coordinates
def get_map_reports():

    connection = get_connection()

    try:
        import pandas as pd

        query = """
            SELECT
                report_id,
                area,
                problem_type,
                description,
                latitude,
                longitude,
                status
            FROM waste_reports
            WHERE latitude IS NOT NULL
            AND longitude IS NOT NULL
        """

        df = pd.read_sql(query, connection)

        return df

    finally:
        connection.close()


        # USER ACOOUNT
import bcrypt


def create_user(full_name, email, password, role="resident", phone=None):

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # Convert password into a secure hash
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        query = """
            INSERT INTO users (
                full_name, email, phone, password_hash, role
            )
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(
            query,
            (full_name, email, phone, password_hash, role)
        )

        connection.commit()

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def verify_user(email, password):

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT *
            FROM users
            WHERE email = %s AND is_active = TRUE
        """

        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if user is None:
            return None

        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            user["password_hash"].encode("utf-8")
        )

        if password_matches:
            user.pop("password_hash", None)
            return user

        return None

    finally:
        cursor.close()
        connection.close()


