# for AI classifier
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import json
from pathlib import Path


import streamlit as st
import pandas as pd
from db import save_waste_report, get_all_reports
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
    page_title="Ilorin Smart Waste",
    page_icon="🌍",
    layout="wide"
)

# Page title
st.title("🌍 Ilorin Smart Waste")
st.subheader("Smarter Waste Management, Cleaner Communities")

st.write(
    "A community-focused prototype designed to help identify "
    "waste disposal problems and areas that may need better "
    "waste collection services."
)

st.warning(
    "DEMO VERSION: The initial records below are simulated. "
    "They are not verified reports from Ilorin."
)

# Sample demonstration data
if "reports" not in st.session_state:
    st.session_state.reports = pd.DataFrame({
        "Area": [
            "Community A",
            "Community B",
            "Community C",
            "Community D",
            "Community E"
        ],
        "Waste_Reports": [15, 8, 22, 5, 18],
        "Collection_Points": [1, 3, 1, 4, 2],
        "Status": [
            "Pending",
            "Resolved",
            "Pending",
            "Pending",
            "In Progress"
        ]
    })

# Navigation
page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Report Waste",
        "Area Analysis",
        "AI Waste Classifier",
        "Waste Map"
    ]
)

# Dashboard

if page == "Dashboard":

    st.title("🌍 Ilorin Smart Waste Dashboard")

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


# Report Waste
# Report Waste
elif page == "Report Waste":

    st.header("Report a Waste Problem")

    st.write(
        "Use this form to report waste disposal problems "
        "in your community."
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
            "Describe the problem"
        )

        submitted = st.form_submit_button(
            "Submit Report"
        )

        if submitted:

            if not area.strip():
                st.error("Please enter an area name.")

            elif not description.strip():
                st.error("Please describe the problem.")

            else:

                try:
                    report_id = save_waste_report(
    area.strip(),
    waste_type,
    description.strip(),
    latitude,
    longitude,
    accuracy
)

                    st.success(
                        f"Report submitted successfully! "
                        f"Your Report ID is {report_id}."
                    )

                except Exception as e:
                    st.error(
                        f"Report submission failed: {e}"
                    )
               

# Area Analysis
elif page == "Area Analysis":

    st.header("Area Analysis")

    reports = st.session_state.reports.copy()

    # Calculate a preliminary priority score
    max_reports = max(
        int(reports["Waste_Reports"].max()),
        1
    )

    reports["Priority_Score"] = (
        reports["Waste_Reports"] / max_reports
        + 1 / (reports["Collection_Points"] + 1)
    ).round(2)

    reports = reports.sort_values(
        by="Priority_Score",
        ascending=False
    )

    st.write(
        "The following ranking is a preliminary screening "
        "tool based on recorded reports and collection-point "
        "counts. It is not an AI prediction."
    )

    st.dataframe(
        reports[
            [
                "Area",
                "Waste_Reports",
                "Collection_Points",
                "Priority_Score",
                "Status"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "A high score suggests an area for further investigation. "
        "Real decisions require verified data on population, "
        "waste volume, facility capacity, accessibility and "
        "community needs."
    )

# AI Waste Classifier
elif page == "AI Waste Classifier":

    st.header("🤖 AI Waste Classifier")

    st.write(
        "Upload an image of waste to identify its category "
        "using our trained AI model."
    )

    st.info(
        "Supported categories: Cardboard, Glass, Metal, "
        "Paper, Plastic and Trash."
    )

    uploaded_file = st.file_uploader(
        "Upload a waste image",
        type=["jpg", "jpeg", "png"]
    )

    if uploaded_file is not None:

        image = Image.open(uploaded_file).convert("RGB")

        st.image(
            image,
            caption="Uploaded Waste Image",
            use_container_width=True
        )

        if st.button("Classify Waste"):

            try:
                # Transform image
                input_tensor = transform(image).unsqueeze(0)

                # Make prediction
                with torch.no_grad():

                    outputs = model(input_tensor)

                    probabilities = torch.softmax(
                        outputs,
                        dim=1
                    )

                    confidence, predicted_index = probabilities.max(
                        dim=1
                    )

                # Get predicted class
                predicted_class = class_names[
                    predicted_index.item()
                ]

                confidence_score = confidence.item() * 100

                # Display results
                st.success(
                    f"Predicted Waste Category: {predicted_class}"
                )

                st.metric(
                    label="Prediction Confidence",
                    value=f"{confidence_score:.2f}%"
                )

                st.caption(
                    "This prediction is generated by the "
                    "Ilorin Smart Waste AI model."
                )

            except Exception as error:

                st.error(
                    f"Classification failed: {error}"
                )


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