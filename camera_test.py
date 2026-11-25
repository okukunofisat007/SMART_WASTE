
import streamlit as st
from PIL import Image

st.set_page_config(page_title="Waste Camera Test")

st.title("Ilorin Smart Waste")
st.subheader("Test the Waste Reporting Camera")

captured_image = st.camera_input(
    "Take a picture of waste"
)

if captured_image is not None:
    image = Image.open(captured_image).convert("RGB")

    st.image(
    image,
    caption="Captured waste image",
    width="stretch"
)

    st.success("Image captured successfully!")
