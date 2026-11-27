
import streamlit as st
from auth import login_user


def show_login():

    st.title("Welcome Back")
    st.subheader("User Login")

    st.write(
        "Sign in to access your Ilorin Smart Waste account."
    )

    with st.form("login_form"):

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        submitted = st.form_submit_button(
            "Sign In",
            use_container_width=True
        )

        if submitted:

            if not email.strip() or not password:
                st.error("Please enter your email and password.")

            else:

                with st.spinner("Verifying your account..."):

                    result = login_user(
                        email.strip(),
                        password
                    )

                if result:

                    st.session_state["user"] = result["user"]
                    st.session_state["access_token"] = result["access_token"]
                    st.session_state["refresh_token"] = result["refresh_token"]
                    st.session_state["authenticated"] = True

                    st.success("Login successful!")
                    st.rerun()

                else:
                    st.error(
                        "Unable to log in. Check your credentials "
                        "or contact the administrator."
                    )