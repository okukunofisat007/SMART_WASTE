
import streamlit as st
from auth import register_user


def show_register():

    st.title("Create Your Account")
    st.subheader("User Registration")

    st.write(
        "Join Ilorin Smart Waste and help build cleaner communities."
    )

    with st.form("registration_form"):

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email"
        )

        phone = st.text_input(
            "Phone Number",
            placeholder="Enter your phone number"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

        if submitted:

            if not full_name.strip() or not email.strip():
                st.error("Please enter your full name and email.")

            elif not password:
                st.error("Please create a password.")

            elif len(password) < 8:
                st.error("Password must contain at least 8 characters.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:

                try:

                    with st.spinner("Creating your account..."):

                        register_user(
                            full_name=full_name.strip(),
                            email=email.strip(),
                            password=password,
                            phone=phone.strip() or None
                        )

                    st.success(
                        "Your account has been created successfully. "
                        "You can now log in."
                    )

                except Exception as e:
                    st.error(f"Registration failed: {e}")
