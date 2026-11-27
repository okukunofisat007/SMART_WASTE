# for AI classifier
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json
from pathlib import Path
import hashlib


import streamlit as st
import pandas as pd
from login import show_login
from auth import logout_user
from db import (
    save_waste_report,
    get_all_reports,
    upload_waste_image,
    save_waste_classification,
    save_recycling_submission,
    get_resident_location,
    save_resident_location
)
from streamlit_geolocation import streamlit_geolocation

import folium
from streamlit_folium import st_folium
from db import get_map_reports

# ==================================
# LOAD AI WASTE CLASSIFICATION MODEL
# ==================================

BASE_DIR = Path(__file__).parent

MODEL_PATH = BASE_DIR / "models" / "ilorin_waste_classifier.pth"

CLASS_NAMES_PATH = BASE_DIR / "models" / "waste_class_names.json"


# Load waste category names
with open(CLASS_NAMES_PATH, "r") as file:
    class_names = json.load(file)


# Create MobileNetV3 Small architecture
model = models.mobilenet_v3_small(weights=None)

# Update final classification layer
model.classifier[3] = nn.Linear(
    model.classifier[3].in_features,
    len(class_names)
)


# Load trained model weights
state_dict = torch.load(
    MODEL_PATH,
    map_location=torch.device("cpu"),
    weights_only=True
)

model.load_state_dict(state_dict)

model.eval()


# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

st.set_page_config(
    page_title="EcoCycly",
    page_icon="♻️",
    layout="wide"
)

# ==================================
# USER AUTHENTICATION
# ==================================

if not st.session_state.get("authenticated", False):
    show_login()
    st.stop()

user = st.session_state["user"]
user_id = user["user_id"]

st.sidebar.write(f"Welcome, {user['full_name']}")

if st.sidebar.button("Logout"):
    logout_user()
    st.rerun()


# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Home",
        "Dashboard",
        "Report Waste",
        "Area Analysis",
        "Waste2Earn",
        "Waste Map"
    ],
    index=0
)

# EcoCycly Home / Landing Page
if page == "Home":

    st.title("♻️ Welcome to EcoCycly")

    st.header("Cleaner Communities Start With Us")

    st.write(
        "EcoCycly is a smart community waste management platform "
        "designed to make waste reporting, monitoring and recycling easier."
    )

    st.markdown("### About EcoCycly")

    st.write(
        "Through image-based waste classification, location tracking "
        "and data analysis, EcoCycly helps residents report waste "
        "disposal problems, monitor community waste challenges and "
        "participate in responsible recycling."
    )

    st.markdown("### What You Can Do With EcoCycly")

    st.markdown("""
    - **Report Waste:** Submit waste reports with pictures and location details.
    - **Monitor Communities:** Explore reports and identify areas with recurring waste challenges.
    - **Waste2Earn:** Submit recyclable materials and earn reward points.
    - **Waste Map:** Explore reported waste locations on an interactive map.
    """)

    st.markdown("### Building Cleaner Communities Together")

    st.write(
        "Every report counts. Every recycling effort matters. "
        "Together, we can build cleaner and more sustainable communities."
    )


# Dashboard

elif page == "Dashboard":

    st.title("Dashboard")

    reports = get_all_reports()

    total_reports = len(reports)

    pending_reports = (
        (reports["status"] == "Pending").sum()
        if not reports.empty else 0
    )

    resolved_reports = (
        (reports["status"] == "Resolved").sum()
        if not reports.empty else 0
    )

    total_areas = (
        reports["area"].nunique()
        if not reports.empty else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Reports", total_reports)
    col2.metric("Pending Reports", pending_reports)
    col3.metric("Resolved Reports", resolved_reports)
    col4.metric("Areas Reporting", total_areas)

    st.subheader("Recent Waste Reports")

    if not reports.empty:

        st.dataframe(
            reports[
                ["report_id", "area", "problem_type",
                 "description", "status", "created_at"]
            ],
            use_container_width=True
        )

    else:
        st.info("No waste reports have been submitted yet.")



elif page == "Report Waste":

    st.title("📸 Report Waste")

    st.write(
        "Help keep your community clean by reporting waste disposal "
        "problems. Add a photo, describe the issue and share its location."
    )


    # GPS LOCATION
    st.subheader("📍 Waste Location")

    location = streamlit_geolocation()

    latitude = None
    longitude = None
    accuracy = None

    if location and location.get("latitude") is not None:

        latitude = location["latitude"]
        longitude = location["longitude"]
        accuracy = location.get("accuracy")

        st.success("Location captured successfully!")

        st.write("Latitude:", latitude)
        st.write("Longitude:", longitude)

        if accuracy is not None:
            st.write("Accuracy:", accuracy, "metres")

    else:
        st.info(
            "Click the location button and allow "
            "your browser to access your location."
        )

    # CAMERA FEATURE
    st.subheader("Capture Waste Image")

    captured_image = st.camera_input(
        "Take a picture of the waste",
        key="waste_report_camera"
    )



    # WASTE REPORT FORM
    with st.form("waste_report_form"):

        area = st.text_input(
            "Community or area name"
        )

        waste_type = st.selectbox(
            "Type of waste problem",
            [
                "Waste dumped in a gutter",
                "Illegal dumping",
                "Overflowing waste collection point",
                "No accessible collection point",
                "Other"
            ]
        )

        description = st.text_area(
            "Describe the problem (Optional)"
        )

        submitted = st.form_submit_button(
            "Submit Report"
        )

        if submitted:

            if captured_image is None:
                st.error("Please take a picture of the waste.")

            elif not area.strip():
                st.error("Please enter an area name.")

            else:
                try:
                    report_id = save_waste_report(
                        area=area.strip(),
                        problem_type=waste_type,
                        description=description.strip(),
                        latitude=latitude,
                        longitude=longitude,
                        accuracy=accuracy,
                        image_bytes=captured_image.getvalue(),
                        image_content_type=captured_image.type,
                        user_id=user_id
                    )

                    st.success(
                        f"Report submitted successfully! "
                        f"Your Report ID is {report_id}."
                    )

                except Exception as e:
                    st.error(f"Report submission failed: {e}")

# ==================================
# AREA ANALYSIS
# ==================================

elif page == "Area Analysis":

    st.header("Area Analysis")

    reports = get_all_reports()

    if reports.empty:

        st.info("No waste reports are available for analysis yet.")

    else:

        # Prepare report data
        reports = reports.copy()

        reports["status"] = (
            reports["status"]
            .fillna("Unknown")
            .str.strip()
            .str.title()
        )

        # Group reports by community
        area_analysis = (
            reports.groupby("area")
            .agg(
                Waste_Reports=("report_id", "count"),
                Pending_Reports=(
                    "status",
                    lambda x: (x == "Pending").sum()
                ),
                Resolved_Reports=(
                    "status",
                    lambda x: (x == "Resolved").sum()
                )
            )
            .reset_index()
            .rename(columns={"area": "Community"})
        )

        # Rank communities by report volume
        area_analysis = area_analysis.sort_values(
            by="Waste_Reports",
            ascending=False
        )

        st.write(
            "This analysis uses actual waste reports submitted "
            "through EcoCycly. Communities are ranked by the "
            "number of reported waste problems."
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Communities Reporting",
            area_analysis["Community"].nunique()
        )

        col2.metric(
            "Total Waste Reports",
            len(reports)
        )

        col3.metric(
            "Pending Reports",
            (reports["status"] == "Pending").sum()
        )

        st.subheader("Community Report Analysis")

        st.dataframe(
            area_analysis,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Waste Reports by Community")

        chart_data = area_analysis.set_index("Community")[
            "Waste_Reports"
        ]

        st.bar_chart(chart_data)

        st.caption(
            "A higher report count indicates more reported waste "
            "problems, not necessarily a higher total waste volume. "
            "Collection-point and population data would be needed "
            "for a more comprehensive community priority assessment."
        )



# ==================================
# WASTE2EARN
# ==================================

elif page == "Waste2Earn":

    st.header("♻️ Waste2Earn")

    st.write(
        "Capture recyclable waste, identify its category "
        "using AI and submit the quantity."
    )


    # ----------------------------------
    # 1. CHECK AND UPDATE RESIDENT LOCATION
    # ----------------------------------

    resident_location = get_resident_location(user_id)

    updating_location = st.session_state.get(
        "update_resident_location", False
    )

    if not resident_location or updating_location:

        if resident_location:
            st.subheader("📍 Update Your Collection Location")

            st.info(
                "Capture your new GPS location and enter your "
                "updated residential address and community."
            )
        else:
            st.subheader("📍 Save Your Residential Location")

            st.info(
                "We need your residential location to arrange "
                "recycling collection. You only need to save it once."
            )

        location = streamlit_geolocation()

        latitude = None
        longitude = None
        accuracy = None

        if location and location.get("latitude") is not None:

            latitude = location["latitude"]
            longitude = location["longitude"]
            accuracy = location.get("accuracy")

            st.success("GPS location captured!")

            st.write("Latitude:", latitude)
            st.write("Longitude:", longitude)

            if accuracy is not None:
                st.write("Accuracy:", accuracy, "metres")

        with st.form("resident_location_form"):

            residential_address = st.text_input(
                "Residential Address",
                value=(
                    resident_location["residential_address"]
                    if resident_location else ""
                ),
                placeholder="Enter your house address"
            )

            area = st.text_input(
                "Community or Area",
                value=(
                    resident_location["area"]
                    if resident_location else ""
                ),
                placeholder="Enter your community"
            )

            save_location = st.form_submit_button(
                "Save New Location" if resident_location
                else "Save My Location"
            )

            if save_location:

                if not residential_address.strip():
                    st.error("Please enter your residential address.")

                elif not area.strip():
                    st.error("Please enter your community.")

                elif latitude is None or longitude is None:
                    st.error(
                        "Please capture your GPS location before saving."
                    )

                else:
                    try:
                        save_resident_location(
                            user_id=user_id,
                            residential_address=residential_address.strip(),
                            area=area.strip(),
                            latitude=latitude,
                            longitude=longitude,
                            accuracy=accuracy
                        )

                        st.session_state.pop(
                            "update_resident_location", None
                        )

                        st.success(
                            "Your collection location has been updated!"
                            if resident_location
                            else "Your residential location has been saved!"
                        )

                        st.rerun()

                    except Exception as error:
                        st.error(
                            f"Location could not be saved: {error}"
                        )

        st.stop()

    else:

        st.subheader("📍 Your Saved Collection Location")

        st.success("Your residential location is saved.")

        st.write(
            "Address:",
            resident_location["residential_address"]
        )

        st.write(
            "Community:",
            resident_location["area"]
        )

        if st.button("📍 Update Collection Location"):

            st.session_state["update_resident_location"] = True
            st.rerun()

        st.divider()

        # ----------------------------------
        # 2. CAPTURE WASTE IMAGE
        # ----------------------------------

        st.subheader("Capture Recyclable Waste")

        captured_image = st.camera_input(
            "Take a picture of your waste",
            key="waste2earn_camera"
        )

        if captured_image is not None:

            image_bytes = captured_image.getvalue()

            image_signature = hashlib.sha256(
                image_bytes
            ).hexdigest()

            # Reset old classification if a new image is captured
            if st.session_state.get("waste2earn_image_signature") != image_signature:

                st.session_state["waste2earn_image_signature"] = image_signature

                st.session_state.pop("predicted_class", None)
                st.session_state.pop("confidence_score", None)

            image = Image.open(captured_image).convert("RGB")

            # ----------------------------------
            # 3. AI CLASSIFICATION
            # ----------------------------------

            if st.button("Classify Waste"):

                try:
                    input_tensor = transform(image).unsqueeze(0)

                    with torch.no_grad():

                        outputs = model(input_tensor)

                        probabilities = torch.softmax(outputs, dim=1)

                        confidence, predicted_index = probabilities.max(dim=1)

                    predicted_class = class_names[predicted_index.item()]

                    # Store confidence as a decimal between 0 and 1
                    confidence_score = confidence.item()

                    st.session_state["predicted_class"] = predicted_class
                    st.session_state["confidence_score"] = confidence_score

                except Exception as error:
                    st.error(f"Classification failed: {error}")

        # ----------------------------------
        # 4. DISPLAY CLASSIFICATION
        # ----------------------------------

        if (
            captured_image is not None
            and st.session_state.get("predicted_class")
        ):

            predicted_class = st.session_state["predicted_class"]
            confidence_score = st.session_state["confidence_score"]

            st.success(f"Identified Waste: {predicted_class}")

            st.metric(
                "Prediction Confidence",
                f"{confidence_score * 100:.2f}%"
            )

            st.divider()

            # ----------------------------------
            # 5. ENTER QUANTITY
            # ----------------------------------

            st.subheader("Enter Waste Quantity")

            quantity_unit = st.selectbox(
                "Select Unit",
                ["Pieces", "kg", "Bags"]
            )

            quantity_text = st.text_input(
                "Enter quantity",
                placeholder="e.g. 5"
            )

            if st.button("Submit to Waste2Earn"):

                if not quantity_text.strip():
                    st.warning("Please enter the quantity.")

                elif not quantity_text.strip().isdigit():
                    st.warning("Please enter a whole number.")

                elif int(quantity_text) <= 0:
                    st.warning("Quantity must be greater than zero.")

                else:
                    try:
                        quantity = int(quantity_text)

                        image_path = upload_waste_image(
                            uploaded_file=captured_image.getvalue(),
                            user_id=user_id,
                            content_type=captured_image.type
                        )

                        classification_id = save_waste_classification(
                            user_id=user_id,
                            category_name=predicted_class,
                            image_path=image_path,
                            confidence_score=confidence_score,
                            model_version="MobileNetV3-Small"
                        )

                        submission_id = save_recycling_submission(
                            user_id=user_id,
                            classification_id=classification_id,
                            quantity=quantity,
                            quantity_unit=quantity_unit
                        )

                        st.success(
                            "Your recycling submission was successful!"
                        )

                        st.write("Submission ID:", submission_id)
                        st.write("Waste Category:", predicted_class)
                        st.write("Quantity:", quantity, quantity_unit)

                    except Exception as error:
                        st.error(f"Submission failed: {error}")

# Waste Map
elif page == "Waste Map":

    st.header("🗺️ Waste Location Map")

    st.write(
        "View reported waste locations across communities."
    )

    reports = get_map_reports()

    if reports.empty:

        st.info("No reports with GPS coordinates available yet.")

    else:

        # Calculate map centre
        center_lat = reports["latitude"].mean()
        center_lon = reports["longitude"].mean()

        waste_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=13
        )

        # Marker colours based on report status
        status_colors = {
            "Pending": "red",
            "Reviewed": "orange",
            "Approved": "blue",
            "Rejected": "gray",
            "Collected": "green",
            "Resolved": "darkgreen"
        }

        for _, row in reports.iterrows():

            color = status_colors.get(
                row["status"],
                "blue"
            )

            popup_text = f"""
            <b>Report ID:</b> {row['report_id']}<br>
            <b>Area:</b> {row['area']}<br>
            <b>Problem:</b> {row['problem_type']}<br>
            <b>Description:</b> {row['description']}<br>
            <b>Status:</b> {row['status']}
            """

            folium.Marker(
                location=[
                    row["latitude"],
                    row["longitude"]
                ],
                popup=folium.Popup(
                    popup_text,
                    max_width=300
                ),
                tooltip=f"Report {row['report_id']}",
                icon=folium.Icon(color=color)
            ).add_to(waste_map)

        st_folium(
            waste_map,
            width=1000,
            height=600
        )

        st.success(
            f"{len(reports)} waste report(s) displayed on the map."
        )