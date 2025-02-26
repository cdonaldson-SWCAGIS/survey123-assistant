"""Tests for Survey123 Assistant API integration."""
import os
from unittest.mock import MagicMock, patch

import pytest
from openai import OpenAI

from assistant.api import AssistantAPI, Message, AssistantResponse


@pytest.fixture
def mock_openai():
    """Mock OpenAI client."""
    with patch("assistant.api.OpenAI") as mock:
        yield mock


@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test-key",
        "OPENAI_ORG_ID": "test-org",
    }):
        yield


@pytest.fixture
def api(mock_openai, mock_env_vars):
    """Create AssistantAPI instance with mocked dependencies."""
    return AssistantAPI()


def test_initialization(api, mock_openai):
    """Test API initialization."""
    assert api.client is not None
    assert api.assistant is None
    assert api.thread is None
    assert api.file_id is None
    mock_openai.assert_called_once_with(
        organization="test-org",
        api_key="test-key",
    )


def test_initialize_assistant(api):
    """Test assistant initialization."""
    mock_file = MagicMock()
    mock_file.id = "test-file-id"
    api.client.files.create = MagicMock(return_value=mock_file)

    mock_assistant = MagicMock()
    api.client.beta.assistants.create = MagicMock(return_value=mock_assistant)

    mock_thread = MagicMock()
    api.client.beta.threads.create = MagicMock(return_value=mock_thread)

    api.initialize("Test instructions")

    assert api.file_id == "test-file-id"
    assert api.assistant == mock_assistant
    assert api.thread == mock_thread

    api.client.files.create.assert_called_once()
    api.client.beta.assistants.create.assert_called_once_with(
        instructions="Test instructions",
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}],
        file_ids=["test-file-id"],
    )
    api.client.beta.threads.create.assert_called_once()


def test_send_message(api):
    """Test sending a message and getting response."""
    # Setup mocks
    api.thread = MagicMock(id="test-thread")
    api.assistant = MagicMock(id="test-assistant")

    mock_message = MagicMock()
    api.client.beta.threads.messages.create = MagicMock(return_value=mock_message)

    mock_run = MagicMock()
    mock_run.status = "completed"
    api.client.beta.threads.runs.create = MagicMock(return_value=mock_run)
    api.client.beta.threads.runs.retrieve = MagicMock(return_value=mock_run)

    mock_messages = [
        MagicMock(
            role="assistant",
            content=[MagicMock(text=MagicMock(value="Test response"))],
            file_ids=[],
        )
    ]
    api.client.beta.threads.messages.list = MagicMock(return_value=mock_messages)

    # Test message sending
    response = api.send_message("Test message")

    assert isinstance(response, AssistantResponse)
    assert len(response.messages) == 1
    assert response.messages[0].role == "assistant"
    assert response.messages[0].content == "Test response"

    # Verify API calls
    api.client.beta.threads.messages.create.assert_called_once_with(
        thread_id="test-thread",
        role="user",
        content="Test message",
    )
    api.client.beta.threads.runs.create.assert_called_once_with(
        thread_id="test-thread",
        assistant_id="test-assistant",
    )


def test_send_message_with_file_output(api):
    """Test sending a message that generates file output."""
    # Setup mocks
    api.thread = MagicMock(id="test-thread")
    api.assistant = MagicMock(id="test-assistant")

    mock_run = MagicMock()
    mock_run.status = "completed"
    api.client.beta.threads.runs.create = MagicMock(return_value=mock_run)
    api.client.beta.threads.runs.retrieve = MagicMock(return_value=mock_run)

    mock_messages = [
        MagicMock(
            role="assistant",
            content=[MagicMock(text=MagicMock(value="Test response"))],
            file_ids=["test-file-id"],
        )
    ]
    api.client.beta.threads.messages.list = MagicMock(return_value=mock_messages)

    mock_file_response = MagicMock()
    mock_file_response.status_code = 200
    mock_file_response.content = b"Test file content"
    api.client.files.with_raw_response.retrieve_content = MagicMock(
        return_value=mock_file_response
    )

    # Test message sending with file output
    response = api.send_message("Test message")

    assert isinstance(response, AssistantResponse)
    assert response.file_ids == ["test-file-id"]
    assert response.output_content == b"Test file content"


def test_send_message_failure(api):
    """Test handling of failed message sending."""
    api.thread = MagicMock(id="test-thread")
    api.assistant = MagicMock(id="test-assistant")

    mock_run = MagicMock()
    mock_run.status = "failed"
    api.client.beta.threads.runs.create = MagicMock(return_value=mock_run)
    api.client.beta.threads.runs.retrieve = MagicMock(return_value=mock_run)

    with pytest.raises(RuntimeError, match="Assistant run failed"):
        api.send_message("Test message")


def test_reset(api):
    """Test conversation reset."""
    api.thread = MagicMock()
    mock_thread = MagicMock()
    api.client.beta.threads.create = MagicMock(return_value=mock_thread)

    api.reset()

    assert api.thread == mock_thread
    api.client.beta.threads.create.assert_called_once()


def test_message_model():
    """Test Message model validation."""
    message = Message(
        role="assistant",
        content="Test content",
        file_ids=["file1", "file2"],
    )
    assert message.role == "assistant"
    assert message.content == "Test content"
    assert message.file_ids == ["file1", "file2"]


def test_assistant_response_model():
    """Test AssistantResponse model validation."""
    messages = [
        Message(role="assistant", content="Test content"),
        Message(role="user", content="Test question"),
    ]
    response = AssistantResponse(
        messages=messages,
        file_ids=["file1"],
        output_content="Test output",
    )
    assert len(response.messages) == 2
    assert response.file_ids == ["file1"]
    assert response.output_content == "Test output"
