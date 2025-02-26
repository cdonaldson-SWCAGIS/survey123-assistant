"""Tests for Survey123 Assistant UI."""
import os
from unittest.mock import MagicMock, patch

import pytest
import streamlit as st

from assistant.ui import (
    initialize_session,
    st_init_null,
    setup_page,
    handle_file_upload,
    display_current_survey,
    handle_chat,
    main,
)
from xlsform_orm import Survey, Question, QuestionTypes


@pytest.fixture
def mock_streamlit():
    """Mock Streamlit functions."""
    with patch("assistant.ui.st") as mock_st:
        yield mock_st


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    with patch.dict(st.session_state, {
        "session_id": "test-session",
        "messages": [],
        "retry_error": 0,
        "api": MagicMock(),
        "file_handler": MagicMock(),
        "request_handler": MagicMock(),
        "run": None,
        "output_content": None,
        "current_survey": None,
        "current_file_path": None,
    }, clear=True):
        yield st.session_state


@pytest.fixture
def basic_survey():
    """Create a basic test survey."""
    return Survey(
        name="test_survey",
        label="Test Survey",
        items=[
            Question(
                type=QuestionTypes.text,
                name="q1",
                label="Question 1"
            )
        ]
    )


def test_initialize_session(mock_session_state):
    """Test session initialization."""
    initialize_session()
    assert "run" in st.session_state
    assert "output_content" in st.session_state
    assert "current_survey" in st.session_state
    assert "current_file_path" in st.session_state


def test_st_init_null(mock_session_state):
    """Test session state variable initialization."""
    st_init_null("test_var1", "test_var2")
    assert st.session_state.test_var1 is None
    assert st.session_state.test_var2 is None


def test_setup_page(mock_streamlit):
    """Test page setup configuration."""
    setup_page()
    mock_streamlit.set_page_config.assert_called_once_with(
        page_title="Survey123 Assistant",
        page_icon="📋",
        layout="wide",
    )
    mock_streamlit.title.assert_called_once()
    mock_streamlit.markdown.assert_called_once()


def test_handle_file_upload_success(mock_streamlit, mock_session_state, basic_survey):
    """Test successful file upload handling."""
    # Mock file uploader
    mock_file = MagicMock()
    mock_file.name = "test.xlsx"
    mock_file.getvalue.return_value = b"test content"
    mock_streamlit.file_uploader.return_value = mock_file

    # Mock file handler
    st.session_state.file_handler.load_survey.return_value = (True, "Success", basic_survey)

    # Test file upload
    with patch("builtins.open", MagicMock()) as mock_open:
        handle_file_upload()

    mock_open.assert_called_once_with("test.xlsx", "wb")
    mock_open().write.assert_called_once_with(b"test content")
    assert st.session_state.current_survey == basic_survey
    assert st.session_state.current_file_path == "test.xlsx"
    mock_streamlit.success.assert_called_once()


def test_handle_file_upload_failure(mock_streamlit, mock_session_state):
    """Test failed file upload handling."""
    # Mock file uploader
    mock_file = MagicMock()
    mock_file.name = "test.xlsx"
    mock_streamlit.file_uploader.return_value = mock_file

    # Mock file handler failure
    st.session_state.file_handler.load_survey.return_value = (False, "Error", None)

    # Test file upload
    with patch("builtins.open", MagicMock()):
        handle_file_upload()

    mock_streamlit.error.assert_called_once()
    assert st.session_state.current_survey is None


def test_display_current_survey(mock_streamlit, mock_session_state, basic_survey):
    """Test current survey display."""
    st.session_state.current_survey = basic_survey

    # Mock expander context
    mock_expander = MagicMock()
    mock_streamlit.expander.return_value.__enter__.return_value = mock_expander

    display_current_survey()

    mock_streamlit.expander.assert_called_once_with("Current Survey", expanded=True)
    assert mock_expander.write.call_count == 3  # name, label, items count


def test_display_current_survey_download(mock_streamlit, mock_session_state, basic_survey, tmp_path):
    """Test survey download functionality."""
    st.session_state.current_survey = basic_survey

    # Mock expander and button
    mock_expander = MagicMock()
    mock_streamlit.expander.return_value.__enter__.return_value = mock_expander
    mock_streamlit.button.return_value = True

    # Mock file handler
    file_path = os.path.join(tmp_path, "test.xlsx")
    st.session_state.file_handler.save_survey.return_value = (True, "Success", file_path)

    # Test download
    with patch("builtins.open", MagicMock()):
        display_current_survey()

    mock_streamlit.download_button.assert_called_once()


def test_handle_chat(mock_streamlit, mock_session_state):
    """Test chat interaction handling."""
    # Mock chat input
    mock_streamlit.chat_input.return_value = "Test message"

    # Mock API response
    mock_message = MagicMock(
        role="assistant",
        content="Test response",
        file_ids=None
    )
    mock_response = MagicMock(
        messages=[mock_message],
        file_ids=None,
        output_content=None
    )
    st.session_state.api.send_message.return_value = mock_response

    # Test chat handling
    handle_chat()

    st.session_state.api.send_message.assert_called_once_with("Test message")
    assert mock_streamlit.chat_message.call_count == 2  # user + assistant


def test_handle_chat_with_file(mock_streamlit, mock_session_state):
    """Test chat interaction with file output."""
    mock_streamlit.chat_input.return_value = "Test message"

    # Mock API response with file
    mock_message = MagicMock(
        role="assistant",
        content="Test response",
        file_ids=["test-file"]
    )
    mock_response = MagicMock(
        messages=[mock_message],
        file_ids=["test-file"],
        output_content="file content"
    )
    st.session_state.api.send_message.return_value = mock_response

    handle_chat()

    mock_streamlit.download_button.assert_called_once_with(
        "Download Output",
        "file content",
        file_name="output.txt",
    )


def test_handle_chat_error(mock_streamlit, mock_session_state):
    """Test chat error handling."""
    mock_streamlit.chat_input.return_value = "Test message"

    # Mock API error
    st.session_state.api.send_message.side_effect = Exception("Test error")

    with patch("time.sleep", MagicMock()):
        handle_chat()

    mock_streamlit.error.assert_called()
    assert st.session_state.retry_error == 1


def test_main(mock_streamlit, mock_session_state):
    """Test main application flow."""
    # Mock sidebar context
    mock_sidebar = MagicMock()
    mock_streamlit.sidebar.return_value.__enter__.return_value = mock_sidebar

    main()

    # Verify initialization and setup
    mock_streamlit.set_page_config.assert_called_once()
    mock_sidebar.header.assert_called_once_with("Survey Options")

    # Verify main content flow
    mock_streamlit.file_uploader.assert_called_once()
    mock_sidebar.button.assert_called_once_with("New Survey")


def test_main_new_survey(mock_streamlit, mock_session_state):
    """Test new survey creation flow."""
    # Mock sidebar and button
    mock_sidebar = MagicMock()
    mock_streamlit.sidebar.return_value.__enter__.return_value = mock_sidebar
    mock_sidebar.button.return_value = True

    # Set current survey
    st.session_state.current_survey = MagicMock()
    st.session_state.current_file_path = "test.xlsx"

    main()

    # Verify survey reset
    assert st.session_state.current_survey is None
    assert st.session_state.current_file_path is None
