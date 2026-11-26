
# ==========================================
# IMPORTS
# ==========================================

import json
import re
import hashlib
from pathlib import Path

import streamlit as st
import pandas as pd
import folium

from PIL import Image
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation

from db import (
    save_waste_report,
    get_all_reports,
    get_user_reports,
    get_user_report_stats,
    get_user_recycling_stats,
    get_map_reports,
    get_waste_categories,
    get_resident_location,
    save_resident_location,
    upload_waste_image,
    save_waste_classification,
    save_recycling_submission
)

from login import show_login
from register import show_register
from auth import logout_user


# ==========================================
# PATHS AND MODEL CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = BASE_DIR / "models" / "ilorin_waste_classifier.pth"

CLASS_NAMES_PATH = BASE_DIR / "models" / "waste_class_names.json"

MODEL_VERSION = "MobileNetV3-Small"


# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Ilorin Smart Waste",
    page_icon="🌍",
    layout="wide"
)


# ==========================================
# LOAD AI MODEL
# ==========================================

@st.cache_resource
def load_waste_model():

    import torch
    import torch.nn as nn
    from torchvision import models, transforms

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found: {MODEL_PATH}"
        )

    if not CLASS_NAMES_PATH.exists():
        raise FileNotFoundError(
            f"Class names file not found: {CLASS_NAMES_PATH}"
        )

    with open(CLASS_NAMES_PATH, "r", encoding="utf-8") as file:
        class_names = json.load(file)

    if isinstance(class_names, dict):
        class_names = list(class_names.values())

    if not isinstance(class_names, list) or not class_names:
        raise ValueError(
            "The class names file must contain a non-empty list."
        )

    model = models.mobilenet_v3_small(weights=None)

    model.classifier[3] = nn.Linear(
        model.classifier[3].in_features,
        len(class_names)
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=torch.device("cpu"),
        weights_only=True
    )

    if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
        checkpoint = checkpoint["state_dict"]

    model.load_state_dict(checkpoint)

    model.eval()

    image_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    return model, class_names, image_transform


# ==========================================
# AI WASTE PREDICTION
# ==========================================

def predict_waste(image):

    import torch

    model, class_names, image_transform = load_waste_model()

    image = image.convert("RGB")

    image_tensor = image_transform(image).unsqueeze(0)

    with torch.no_grad():

        outputs = model(image_tensor)

        probabilities = torch.softmax(outputs, dim=1)

        confidence, predicted_index = torch.max(
            probabilities,
            dim=1
        )

    predicted_class = class_names[predicted_index.item()]

    confidence_score = confidence.item()

    return predicted_class, confidence_score


# ==========================================
# NORMALIZE CATEGORY NAME
# ==========================================

def normalize_category_name(name):

    name = str(name).lower().strip()

    name = re.sub(r"[_\-]+", " ", name)

    name = re.sub(r"\s+", " ", name)

    return name


# ==========================================
# MATCH AI PREDICTION WITH DATABASE CATEGORY
# ==========================================

def match_database_category(predicted_class, categories):

    predicted_name = normalize_category_name(predicted_class)

    # The database function returns a DataFrame.
    if isinstance(categories, pd.DataFrame):
        category_records = categories.to_dict("records")
    else:
        category_records = categories or []

    for category in category_records:

        database_name = normalize_category_name(
            category["category_name"]
        )

        if predicted_name == database_name:
            return category

        if predicted_name.startswith(database_name + " "):
            return category

        if database_name in predicted_name:
            return category

    return None


# ==========================================
# AUTHENTICATION CONTROL
# ==========================================

if "authenticated" not in st.session_state:

    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:

    st.title("🌍 Ilorin Smart Waste")

    st.sidebar.title("Account")

    auth_page = st.sidebar.radio(
        "Choose an option",
        ["User Login", "Create Account"]
    )

    if auth_page == "User Login":
        show_login()

    else:
        show_register()

    st.stop()


# ==========================================
# LOGGED-IN USER INFORMATION
# ==========================================

current_user = st.session_state.get("user")

if not current_user:

    logout_user()

    st.rerun()

user_id = str(current_user["user_id"])

user_role = current_user["role"].lower()


# ==========================================
# SIDEBAR
# ==========================================

st.sidebar.title("🌍 Ilorin Smart Waste")

st.sidebar.success(
    f"Welcome, {current_user['full_name']}"
)

st.sidebar.caption(
    f"Account type: {user_role.capitalize()}"
)

if st.sidebar.button(
    "Logout",
    use_container_width=True
):

    logout_user()

    st.rerun()


# ==========================================
# ROLE-BASED NAVIGATION
# ==========================================

if user_role == "admin":

    navigation_options = [
        "Admin Dashboard",
        "Area Analysis",
        "Waste Map"
    ]

elif user_role == "user":

    navigation_options = [
        "Dashboard",
        "Report Waste",
        "AI Waste Classifier"
    ]

else:

    st.warning(
        "The collector dashboard is not available yet."
    )

    st.info(
        "Collector features will be added in the next development stage."
    )

    st.stop()

page = st.sidebar.radio(
    "Navigation",
    navigation_options
)


# ==========================================
# APPLICATION INTRODUCTION
# ==========================================

st.title("🌍 Ilorin Smart Waste")

st.subheader(
    "Smarter Waste Management, Cleaner Communities"
)

st.write(
    "A community-focused platform designed to improve "
    "waste reporting, identification and collection "
    "across communities in Ilorin."
)


# ==========================================
# RESIDENT DASHBOARD
# ==========================================

if page == "Dashboard":

    st.header("Resident Dashboard")

    st.write(
        "Monitor your recycling contributions, earned points "
        "and waste reports."
    )

    try:

        reports = get_user_reports(user_id)

        if reports is None:
            reports = pd.DataFrame()

        recycling_stats = get_user_recycling_stats(user_id)

        report_stats = get_user_report_stats(user_id)

        total_points = recycling_stats["total_points"]

        total_bottles = recycling_stats["total_bottles"]

        total_reports = report_stats["total_reports"]

        pending_reports = report_stats["pending_reports"]

        in_progress_reports = report_stats["in_progress_reports"]

        resolved_reports = report_stats["resolved_reports"]

        st.subheader("My Recycling Summary")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "🏆 Total Points Earned",
            f"{total_points:,}"
        )

        col2.metric(
            "♻️ Bottles Submitted",
            f"{total_bottles:,}"
        )

        col3.metric(
            "📋 Total Waste Reports",
            f"{total_reports:,}"
        )

        st.divider()

        st.subheader("Waste Report Status")

        col1, col2, col3 = st.columns(3)

        col1.metric("Pending", pending_reports)

        col2.metric("In Progress", in_progress_reports)

        col3.metric("Resolved", resolved_reports)

        st.divider()

        st.subheader("My Recent Waste Reports")

        if not reports.empty:

            display_columns = [
                column for column in [
                    "report_id",
                    "area",
                    "problem_type",
                    "description",
                    "status",
                    "created_at"
                ]
                if column in reports.columns
            ]

            st.dataframe(
                reports[display_columns].head(10),
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "You have not submitted any waste reports yet."
            )

        st.divider()

        st.subheader("My Recycling Activity")

        st.write(
            f"Total recycling submissions: "
            f"{recycling_stats['total_submissions']}"
        )

        st.caption(
            "Only awarded points count towards your total points."
        )

    except Exception as e:

        st.error(
            f"Could not load your dashboard: {e}"
        )


# ==========================================
# REPORT WASTE
# ==========================================

elif page == "Report Waste":

    st.header("Report a Waste Problem")

    st.write(
        "Capture a photo of the waste problem in your community "
        "and submit its details."
    )

    st.subheader("Capture Waste Photo")

    camera_image = st.camera_input(
        "Take a picture of the waste problem",
        key="report_waste_camera"
    )

    if camera_image is not None:

        st.success(
            "Waste photo captured successfully."
        )

        st.image(
            camera_image,
            caption="Captured Waste Problem",
            use_container_width=True
        )

    else:

        st.info(
            "Use your camera to take a picture of the waste problem "
            "before submitting your report."
        )

    st.divider()

    st.subheader("Waste Location")

    location = streamlit_geolocation()

    latitude = None
    longitude = None
    accuracy = None

    if location and location.get("latitude") is not None:

        latitude = location["latitude"]

        longitude = location["longitude"]

        accuracy = location.get("accuracy")

        st.success("Location captured successfully!")

        col1, col2 = st.columns(2)

        col1.write(f"Latitude: {latitude}")

        col2.write(f"Longitude: {longitude}")

        if accuracy is not None:

            st.caption(
                f"Location accuracy: {accuracy} metres"
            )

    else:

        st.info(
            "Allow location access in your browser to capture "
            "the waste problem's GPS coordinates. You can still "
            "submit a report without GPS coordinates."
        )

    st.divider()

    st.subheader("Waste Problem Details")

    with st.form("waste_report_form"):

        area = st.text_input(
            "Community or area name",
            placeholder="Enter your community or area"
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
            "Describe the problem",
            placeholder="Provide details about the waste problem..."
        )

        submitted = st.form_submit_button(
            "Submit Waste Report",
            use_container_width=True
        )

        if submitted:

            if camera_image is None:

                st.error(
                    "Please take a picture before submitting."
                )

            elif not area.strip():

                st.error(
                    "Please enter an area name."
                )

            elif not description.strip():

                st.error(
                    "Please describe the waste problem."
                )

            else:

                try:

                    with st.spinner(
                        "Uploading photo and saving your report..."
                    ):

                        image_path = upload_waste_image(
                            camera_image,
                            user_id
                        )

                        report_id = save_waste_report(
                            area=area.strip(),
                            problem_type=waste_type,
                            description=description.strip(),
                            latitude=latitude,
                            longitude=longitude,
                            accuracy=accuracy,
                            user_id=user_id,
                            image_path=image_path
                        )

                    st.success(
                        f"Your waste report was submitted successfully! "
                        f"Report ID: {report_id}"
                    )

                    st.info(
                        "Your report is now awaiting review."
                    )

                except Exception as e:

                    st.error(
                        f"Report submission failed: {e}"
                    )


# ==========================================
# AI WASTE CLASSIFIER
# ==========================================

elif page == "AI Waste Classifier":

    st.header("🤖 AI Waste Classifier")

    st.write(
        "Capture your waste using the camera. "
        "Our AI model will automatically identify the material."
    )

    st.subheader("Capture Waste Image")

    camera_image = st.camera_input(
        "Take a picture of your waste item",
        key="classifier_camera"
    )

    if camera_image is None:

        st.info(
            "Take a picture of your waste item to begin."
        )

        st.stop()

    image_bytes = camera_image.getvalue()

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    image = Image.open(camera_image).convert("RGB")

    st.image(
        image,
        caption="Captured Waste Image",
        use_container_width=True
    )

    prediction = st.session_state.get("waste_prediction")

    if prediction is None or prediction.get("image_hash") != image_hash:

        try:

            with st.spinner(
                "AI is analysing your waste image..."
            ):

                predicted_class, confidence_score = predict_waste(
                    image.copy()
                )

                categories = get_waste_categories()

                matched_category = match_database_category(
                    predicted_class,
                    categories
                )

                prediction = {
                    "predicted_class": predicted_class,
                    "confidence_score": confidence_score,
                    "category": matched_category,
                    "image_bytes": image_bytes,
                    "image_hash": image_hash
                }

                st.session_state["waste_prediction"] = prediction

        except Exception as e:

            st.error(
                f"Image classification failed: {e}"
            )

            st.stop()

    prediction = st.session_state["waste_prediction"]

    predicted_class = prediction["predicted_class"]

    confidence_score = prediction["confidence_score"]

    matched_category = prediction["category"]

    st.divider()

    st.subheader("AI Classification Result")

    col1, col2 = st.columns(2)

    col1.metric(
        "Predicted Material",
        predicted_class.replace("_", " ").title()
    )

    col2.metric(
        "Confidence",
        f"{confidence_score * 100:.2f}%"
    )

    if matched_category is None:

        st.error(
            "The AI prediction does not match any active "
            "waste category in your database. "
            "Check your model class names and waste_categories table."
        )

        st.stop()

    category_name = matched_category["category_name"]

    is_recyclable = matched_category["is_recyclable"]

    st.write(f"**Database category:** {category_name}")

    # ======================================
    # RECYCLABLE WASTE
    # ======================================

    if is_recyclable:

        st.success(
            f"{category_name} is recyclable."
        )

        st.divider()

        st.subheader("Pickup Location")

        try:

            resident_location = get_resident_location(user_id)

        except Exception as e:

            st.error(
                f"Could not check your saved location: {e}"
            )

            st.stop()

        # ----------------------------------
        # FIRST-TIME LOCATION REGISTRATION
        # ----------------------------------

        if resident_location is None:

            st.info(
                "This is your first recycling submission. "
                "We need to capture your residential location once. "
                "Your saved location will be reused for future submissions."
            )

            st.write(
                "Allow your browser to access your location."
            )

            location = streamlit_geolocation()

            latitude = None
            longitude = None
            accuracy = None

            if location and location.get("latitude") is not None:

                latitude = location.get("latitude")

                longitude = location.get("longitude")

                accuracy = location.get("accuracy")

                st.success(
                    "Your GPS location has been captured."
                )

                col1, col2 = st.columns(2)

                col1.write(f"Latitude: {latitude}")

                col2.write(f"Longitude: {longitude}")

                if accuracy is not None:

                    st.caption(
                        f"GPS accuracy: {accuracy} metres"
                    )

            else:

                st.warning(
                    "Your GPS location has not been captured yet. "
                    "Allow location permission in your browser."
                )

            st.divider()

            st.subheader("Residential Details")

            with st.form("first_recycling_location_form"):

                residential_address = st.text_input(
                    "Residential Address",
                    placeholder="Enter your house number and street"
                )

                residential_area = st.text_input(
                    "Community / Area",
                    placeholder="Enter your community or area"
                )

                number_of_bottles = st.number_input(
                    "Number of bottles",
                    min_value=1,
                    max_value=10000,
                    value=1,
                    step=1
                )

                submit_recycling = st.form_submit_button(
                    "Submit Recycling",
                    type="primary",
                    use_container_width=True
                )

            if submit_recycling:

                if latitude is None or longitude is None:

                    st.error(
                        "GPS location is required. Please allow "
                        "location access in your browser and try again."
                    )

                elif not residential_address.strip():

                    st.error(
                        "Please enter your residential address."
                    )

                elif not residential_area.strip():

                    st.error(
                        "Please enter your community or area."
                    )

                else:

                    try:

                        with st.spinner(
                            "Saving your location and recycling submission..."
                        ):

                            save_resident_location(
                                user_id=user_id,
                                residential_address=residential_address,
                                area=residential_area,
                                latitude=latitude,
                                longitude=longitude,
                                accuracy=accuracy
                            )

                            image_path = upload_waste_image(
                                prediction["image_bytes"],
                                user_id,
                                file_name="camera_capture.jpg"
                            )

                            classification_id = save_waste_classification(
                                user_id=user_id,
                                category_name=category_name,
                                image_path=image_path,
                                confidence_score=confidence_score,
                                model_version=MODEL_VERSION
                            )

                            submission_id = save_recycling_submission(
                                user_id=user_id,
                                classification_id=classification_id,
                                number_of_bottles=int(number_of_bottles)
                            )

                        st.success(
                            "Your location and recycling submission "
                            "were saved successfully!"
                        )

                        st.write(
                            f"**Waste category:** {category_name}"
                        )

                        st.write(
                            f"**Number of bottles:** {int(number_of_bottles)}"
                        )

                        st.write(
                            f"**Submission ID:** {submission_id}"
                        )

                        st.info(
                            "Your submission is awaiting verification. "
                            "Points will be added to your dashboard "
                            "when they are awarded."
                        )

                        st.session_state.pop(
                            "waste_prediction",
                            None
                        )

                        st.session_state.pop(
                            "number_of_bottles",
                            None
                        )

                        st.rerun()

                    except Exception as e:

                        st.error(
                            f"Recycling submission failed: {e}"
                        )

        # ----------------------------------
        # SUBSEQUENT RECYCLING SUBMISSIONS
        # ----------------------------------

        else:

            st.success(
                "Your residential location is already saved."
            )

            st.write(
                f"**Address:** {resident_location['residential_address']}"
            )

            st.write(
                f"**Area:** {resident_location['area']}"
            )

            st.caption(
                "Your saved pickup location will be used automatically."
            )

            st.divider()

            st.subheader("Recycling Quantity")

            number_of_bottles = st.number_input(
                "Number of bottles",
                min_value=1,
                max_value=10000,
                value=1,
                step=1,
                key="number_of_bottles"
            )

            st.caption(
                "Enter the number of bottles you are submitting."
            )

            if st.button(
                "Submit Recycling",
                type="primary",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Saving your recycling submission..."
                    ):

                        image_path = upload_waste_image(
                            prediction["image_bytes"],
                            user_id,
                            file_name="camera_capture.jpg"
                        )

                        classification_id = save_waste_classification(
                            user_id=user_id,
                            category_name=category_name,
                            image_path=image_path,
                            confidence_score=confidence_score,
                            model_version=MODEL_VERSION
                        )

                        submission_id = save_recycling_submission(
                            user_id=user_id,
                            classification_id=classification_id,
                            number_of_bottles=int(number_of_bottles)
                        )

                    st.success(
                        "Your recycling submission was saved successfully!"
                    )

                    st.write(
                        f"**Waste category:** {category_name}"
                    )

                    st.write(
                        f"**Number of bottles:** {int(number_of_bottles)}"
                    )

                    st.write(
                        f"**Submission ID:** {submission_id}"
                    )

                    st.info(
                        "Your submission is awaiting verification. "
                        "Points will be added to your dashboard "
                        "when they are awarded."
                    )

                    st.session_state.pop(
                        "waste_prediction",
                        None
                    )

                    st.session_state.pop(
                        "number_of_bottles",
                        None
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Recycling submission failed: {e}"
                    )

    # ======================================
    # NON-RECYCLABLE WASTE
    # ======================================

    else:

        st.warning(
            f"{category_name} is not marked as recyclable."
        )

        st.write(
            "You can save the AI classification for record-keeping, "
            "but it cannot be submitted as a recycling request."
        )

        if st.button(
            "Save Waste Classification",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Saving waste classification..."
                ):

                    image_path = upload_waste_image(
                        prediction["image_bytes"],
                        user_id,
                        file_name="camera_capture.jpg"
                    )

                    classification_id = save_waste_classification(
                        user_id=user_id,
                        category_name=category_name,
                        image_path=image_path,
                        confidence_score=confidence_score,
                        model_version=MODEL_VERSION
                    )

                st.success(
                    "Waste classification saved successfully!"
                )

                st.write(
                    f"Classification ID: {classification_id}"
                )

                st.session_state.pop(
                    "waste_prediction",
                    None
                )

                st.rerun()

            except Exception as e:

                st.error(
                    f"Could not save classification: {e}"
                )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

elif page == "Admin Dashboard":

    st.header("Admin Dashboard")

    try:

        reports = get_all_reports()

        if reports is None:
            reports = pd.DataFrame()

        total_reports = len(reports)

        if not reports.empty:

            statuses = (
                reports["status"]
                .fillna("")
                .astype(str)
                .str.lower()
            )

            pending_reports = int(
                statuses.eq("pending").sum()
            )

            in_progress_reports = int(
                statuses.eq("in progress").sum()
            )

            resolved_reports = int(
                statuses.eq("resolved").sum()
            )

            total_areas = reports["area"].nunique()

        else:

            pending_reports = 0
            in_progress_reports = 0
            resolved_reports = 0
            total_areas = 0

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Reports", total_reports)

        col2.metric("Pending Reports", pending_reports)

        col3.metric("Resolved Reports", resolved_reports)

        col4.metric("Areas Reporting", total_areas)

        st.divider()

        st.subheader("All Waste Reports")

        if not reports.empty:

            display_columns = [
                column for column in [
                    "report_id",
                    "user_id",
                    "area",
                    "problem_type",
                    "description",
                    "image_path",
                    "status",
                    "created_at"
                ]
                if column in reports.columns
            ]

            st.dataframe(
                reports[display_columns],
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No waste reports have been submitted yet."
            )

    except Exception as e:

        st.error(
            f"Could not load admin dashboard: {e}"
        )


# ==========================================
# AREA ANALYSIS
# ==========================================

elif page == "Area Analysis":

    st.header("Area Analysis")

    st.write(
        "Review reported waste problems across different "
        "communities and identify areas with higher reporting activity."
    )

    try:

        reports = get_all_reports()

        if reports.empty:

            st.info(
                "No waste reports are available for area analysis."
            )

        else:

            area_analysis = (
                reports.groupby("area")
                .agg(
                    Total_Reports=("report_id", "count")
                )
                .reset_index()
                .rename(
                    columns={"area": "Area"}
                )
            )

            area_analysis = area_analysis.sort_values(
                by="Total_Reports",
                ascending=False
            )

            st.subheader("Reports by Area")

            st.dataframe(
                area_analysis,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Waste Reports Across Communities")

            chart_data = area_analysis.set_index("Area")

            st.bar_chart(
                chart_data["Total_Reports"]
            )

            st.caption(
                "Areas with more reports have higher recorded reporting "
                "activity. This does not necessarily mean they generate "
                "more waste or have the highest collection demand."
            )

    except Exception as e:

        st.error(
            f"Could not load area analysis: {e}"
        )


# ==========================================
# WASTE MAP
# ==========================================

elif page == "Waste Map":

    st.header("🗺️ Waste Location Map")

    st.write(
        "View reported waste locations across communities."
    )

    try:

        reports = get_map_reports()

        if reports.empty:

            st.info(
                "No reports with GPS coordinates are available yet."
            )

        else:

            reports = reports.dropna(
                subset=["latitude", "longitude"]
            )

            if reports.empty:

                st.info(
                    "No valid GPS coordinates are available."
                )

            else:

                center_lat = reports["latitude"].mean()

                center_lon = reports["longitude"].mean()

                waste_map = folium.Map(
                    location=[
                        center_lat,
                        center_lon
                    ],
                    zoom_start=13
                )

                status_colors = {
                    "Pending": "red",
                    "Reviewed": "orange",
                    "Approved": "blue",
                    "Rejected": "gray",
                    "Collected": "green",
                    "Resolved": "darkgreen",
                    "In Progress": "orange"
                }

                for _, row in reports.iterrows():

                    status = str(
                        row.get("status", "Pending")
                    )

                    color = status_colors.get(
                        status,
                        "blue"
                    )

                    popup_text = f"""
                    <b>Report ID:</b> {row['report_id']}<br>
                    <b>Area:</b> {row['area']}<br>
                    <b>Problem:</b> {row['problem_type']}<br>
                    <b>Description:</b> {row.get('description', '')}<br>
                    <b>Status:</b> {status}
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
                        icon=folium.Icon(
                            color=color
                        )
                    ).add_to(waste_map)

                st_folium(
                    waste_map,
                    width=1000,
                    height=600
                )

                st.success(
                    f"{len(reports)} waste report(s) displayed on the map."
                )

    except Exception as e:

        st.error(
            f"Could not load waste map: {e}"
        )
