"""Streamlit UI for Survey123 Assistant."""
import os
import time
import uuid
from typing import Dict, Optional

import streamlit as st

from assistant.api import AssistantAPI
from assistant.handlers import FileHandler, RequestHandler, SurveyRequest

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "retry_error" not in st.session_state:
    st.session_state.retry_error = 0

if "api" not in st.session_state:
    st.session_state.api = AssistantAPI()

if "file_handler" not in st.session_state:
    st.session_state.file_handler = FileHandler()

if "request_handler" not in st.session_state:
    st.session_state.request_handler = RequestHandler()


def initialize_session() -> None:
    """Initialize session variables."""
    st_init_null(
        "run",
        "output_content",
        "current_survey",
        "current_file_path",
    )


def st_init_null(*variable_names: str) -> None:
    """Initialize session state variables to None."""
    for variable_name in variable_names:
        if variable_name not in st.session_state:
            st.session_state[variable_name] = None


def setup_page() -> None:
    """Configure page settings."""
    st.set_page_config(
        page_title="Survey123 Assistant",
        page_icon="📋",
        layout="wide",
    )
    st.title("Survey123 Assistant")
    st.markdown(
        """
        Create and modify Survey123 forms using natural language.
        Upload existing forms or create new ones from scratch.
        """
    )


def handle_file_upload() -> None:
    """Handle survey file upload."""
    uploaded_file = st.file_uploader(
        "Upload a survey file (Excel or YAML)",
        type=["xlsx", "yaml"],
    )
    if uploaded_file:
        # Save uploaded file
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getvalue())

        # Load survey
        success, message, survey = st.session_state.file_handler.load_survey(
            uploaded_file.name
        )

        if success:
            st.session_state.current_survey = survey
            st.session_state.current_file_path = uploaded_file.name
            st.success(message)
        else:
            st.error(message)


def display_current_survey() -> None:
    """Display current survey information."""
    if st.session_state.current_survey:
        with st.expander("Current Survey", expanded=True):
            st.write(f"Name: {st.session_state.current_survey.name}")
            st.write(f"Label: {st.session_state.current_survey.label}")
            st.write(f"Number of items: {len(st.session_state.current_survey.items)}")

            if st.button("Download Survey"):
                success, message, file_path = st.session_state.file_handler.save_survey(
                    st.session_state.current_survey,
                    format="excel",
                )
                if success:
                    with open(file_path, "rb") as f:
                        st.download_button(
                            "Download Excel File",
                            f,
                            file_name=f"{st.session_state.current_survey.name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        )
                else:
                    st.error(message)


def handle_chat() -> None:
    """Handle chat interaction."""
    # Initialize API if needed
    if not st.session_state.api.assistant:
        with open("instructions.txt") as f:
            instructions = f.read()
        st.session_state.api.initialize(instructions)

    # Chat input
    if prompt := st.chat_input("How can I help you create or modify your survey?"):
        # Add user message to chat
        with st.chat_message("user"):
            st.write(prompt)

        # Get assistant response
        try:
            response = st.session_state.api.send_message(prompt)

            # Display assistant messages
            for message in response.messages:
                with st.chat_message(message.role):
                    st.write(message.content)

                    # Handle file output if any
                    if message.file_ids and response.output_content:
                        st.download_button(
                            "Download Output",
                            response.output_content,
                            file_name="output.txt",
                        )

        except Exception as e:
            st.error(f"Error: {str(e)}")
            if st.session_state.retry_error < 3:
                st.session_state.retry_error += 1
                time.sleep(1)
                st.rerun()
            else:
                st.error(
                    "Failed to get response from the assistant. Please try again later."
                )


def main() -> None:
    """Main application entry point."""
    initialize_session()
    setup_page()

    # Sidebar
    with st.sidebar:
        st.header("Survey Options")
        handle_file_upload()
        if st.button("New Survey"):
            st.session_state.current_survey = None
            st.session_state.current_file_path = None

    # Main content
    display_current_survey()
    handle_chat()


if __name__ == "__main__":
    main()
