
import streamlit as st
import pandas as pd

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
        "Area Analysis"
    ]
)

# Dashboard
if page == "Dashboard":

    st.header("Waste Management Dashboard")

    reports = st.session_state.reports

    total_reports = int(reports["Waste_Reports"].sum())

    pending_reports = int(
        (reports["Status"] == "Pending").sum()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Recorded Waste Reports",
        total_reports
    )

    col2.metric(
        "Areas Monitored",
        len(reports)
    )

    col3.metric(
        "Pending Area Records",
        pending_reports
    )

    st.subheader("Waste Management Records")

    st.dataframe(
        reports,
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "These figures use simulated demonstration data. "
        "They do not represent actual citywide waste statistics."
    )

# Report Waste
elif page == "Report Waste":

    st.header("Report a Waste Problem")

    st.write(
        "Use this form to demonstrate how residents could "
        "report waste disposal problems."
    )

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

                new_report = pd.DataFrame([{
                    "Area": area.strip(),
                    "Waste_Reports": 1,
                    "Collection_Points": 0,
                    "Status": "Pending"
                }])

                st.session_state.reports = pd.concat(
                    [
                        st.session_state.reports,
                        new_report
                    ],
                    ignore_index=True
                )

                st.success(
                    "Demonstration report submitted successfully!"
                )

                st.info(
                    f"Problem type: {waste_type}. "
                    "This prototype stores the report in the "
                    "current application session. It does not "
                    "automatically notify waste management authorities."
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

st.divider()

st.caption(
    "Ilorin Smart Waste | Environmental Innovation Prototype"
)
