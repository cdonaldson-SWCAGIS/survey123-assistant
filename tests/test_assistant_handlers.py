"""Tests for Survey123 Assistant request and response handlers."""

import os
import tempfile
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from assistant.handlers import (
    SurveyRequest,
    SurveyResponse,
    RequestHandler,
    FileHandler,
)
from xlsform_orm import Survey, Question, QuestionGroup, Choice, QuestionTypes


@pytest.fixture
def basic_survey():
    """Create a basic test survey."""
    return Survey(
        name="test_survey",
        label="Test Survey",
        items=[Question(type=QuestionTypes.text, name="q1", label="Question 1")],
    )


@pytest.fixture
def survey_request():
    """Create a basic survey request."""
    return SurveyRequest(
        action="create",
        survey_name="test_survey",
        survey_label="Test Survey",
        questions=[
            {"type": "text", "name": "q1", "label": "Question 1"},
            {
                "type": "select_one",
                "name": "q2",
                "label": "Question 2",
                "choices": [
                    {"value": "a", "label": "Option A"},
                    {"value": "b", "label": "Option B"},
                ],
            },
        ],
        groups=[
            {
                "name": "group1",
                "label": "Group 1",
                "items": [{"type": "text", "name": "q3", "label": "Question 3"}],
            }
        ],
    )


def test_survey_request_validation():
    """Test SurveyRequest model validation."""
    # Test valid request
    request = SurveyRequest(action="create")
    assert request.action == "create"
    assert request.survey_name is None
    assert request.questions is None

    # Test with all fields
    request = SurveyRequest(
        action="create",
        survey_name="test",
        survey_label="Test",
        questions=[{"type": "text", "name": "q1", "label": "Q1"}],
        groups=[{"name": "g1", "label": "G1", "items": []}],
        file_path="test.xlsx",
    )
    assert request.survey_name == "test"
    assert len(request.questions) == 1
    assert len(request.groups) == 1


def test_survey_response_validation():
    """Test SurveyResponse model validation."""
    # Test successful response
    response = SurveyResponse(
        success=True,
        message="Success",
        survey=Survey(name="test", label="Test", items=[]),
        file_path="test.xlsx",
    )
    assert response.success
    assert response.message == "Success"
    assert response.survey is not None
    assert response.error is None

    # Test error response
    response = SurveyResponse(success=False, message="Failed", error="Error message")
    assert not response.success
    assert response.error == "Error message"
    assert response.survey is None


def test_request_handler_create_survey(survey_request):
    """Test survey creation through RequestHandler."""
    handler = RequestHandler()
    response = handler.create_survey(survey_request)

    assert response.success
    assert response.survey is not None
    assert len(response.survey.items) == 3  # 2 questions + 1 group
    assert isinstance(response.survey.items[0], Question)
    assert isinstance(response.survey.items[1], Question)
    assert isinstance(response.survey.items[2], QuestionGroup)


def test_request_handler_create_survey_with_file(survey_request, tmp_path):
    """Test survey creation with file output."""
    file_path = os.path.join(tmp_path, "test_survey.xlsx")
    survey_request.file_path = file_path

    handler = RequestHandler()
    response = handler.create_survey(survey_request)

    assert response.success
    assert response.file_path == file_path
    assert os.path.exists(file_path)


def test_request_handler_modify_survey(basic_survey, tmp_path):
    """Test survey modification through RequestHandler."""
    # Save initial survey
    file_path = os.path.join(tmp_path, "test_survey.xlsx")
    basic_survey.save_to_excel(file_path)

    # Create modification request
    request = SurveyRequest(
        action="modify",
        file_path=file_path,
        questions=[{"type": "text", "name": "q2", "label": "New Question"}],
    )

    handler = RequestHandler()
    response = handler.modify_survey(request)

    assert response.success
    assert len(response.survey.items) == 2
    assert response.survey.items[1].name == "q2"


def test_request_handler_invalid_request():
    """Test handling of invalid requests."""
    handler = RequestHandler()

    # Missing required file path for modification
    request = SurveyRequest(action="modify")
    response = handler.modify_survey(request)
    assert not response.success
    assert "File path required" in response.message


def test_file_handler_save_survey(basic_survey):
    """Test saving survey through FileHandler."""
    handler = FileHandler()

    # Test Excel format
    success, message, file_path = handler.save_survey(basic_survey, format="excel")
    assert success
    assert os.path.exists(file_path)
    assert file_path.endswith(".xlsx")

    # Test YAML format
    success, message, file_path = handler.save_survey(basic_survey, format="yaml")
    assert success
    assert os.path.exists(file_path)
    assert file_path.endswith(".yaml")

    # Cleanup
    os.unlink(file_path)


def test_file_handler_load_survey(basic_survey, tmp_path):
    """Test loading survey through FileHandler."""
    handler = FileHandler()

    # Test Excel format
    excel_path = os.path.join(tmp_path, "test.xlsx")
    basic_survey.save_to_excel(excel_path)
    success, message, loaded_survey = handler.load_survey(excel_path)
    assert success
    assert loaded_survey.name == basic_survey.name

    # Test YAML format
    yaml_path = os.path.join(tmp_path, "test.yaml")
    basic_survey.save_to_yaml(yaml_path)
    success, message, loaded_survey = handler.load_survey(yaml_path)
    assert success
    assert loaded_survey.name == basic_survey.name


def test_file_handler_invalid_file():
    """Test handling of invalid files."""
    handler = FileHandler()

    # Non-existent file
    success, message, survey = handler.load_survey("nonexistent.xlsx")
    assert not success
    assert survey is None

    # Invalid format
    success, message, survey = handler.load_survey("test.txt")
    assert not success
    assert "Unsupported file format" in message


def test_request_handler_create_complex_survey():
    """Test creation of a complex survey with various question types."""
    request = SurveyRequest(
        action="create",
        survey_name="complex_survey",
        survey_label="Complex Survey",
        questions=[
            {"type": "text", "name": "name", "label": "Your name", "required": True},
            {
                "type": "select_multiple",
                "name": "interests",
                "label": "Your interests",
                "choices": [
                    {"value": "tech", "label": "Technology"},
                    {"value": "art", "label": "Art"},
                    {"value": "science", "label": "Science"},
                ],
                "allow_other": True,
            },
            {
                "type": "range",
                "name": "age",
                "label": "Your age",
                "range": {"start": 18, "end": 100, "step": 1},
            },
        ],
        groups=[
            {
                "name": "contact",
                "label": "Contact Information",
                "type": "group",
                "items": [
                    {"type": "email", "name": "email", "label": "Email address"},
                    {"type": "text", "name": "phone", "label": "Phone number"},
                ],
            },
            {
                "name": "education",
                "label": "Education",
                "type": "repeat",
                "repeat_count": 3,
                "items": [
                    {
                        "type": "text",
                        "name": "institution",
                        "label": "Institution name",
                    },
                    {"type": "date", "name": "graduation", "label": "Graduation date"},
                ],
            },
        ],
    )

    handler = RequestHandler()
    response = handler.create_survey(request)

    assert response.success
    assert response.survey is not None
    assert len(response.survey.items) == 5  # 3 questions + 2 groups

    # Verify question types and attributes
    questions = [item for item in response.survey.items if isinstance(item, Question)]
    groups = [item for item in response.survey.items if isinstance(item, QuestionGroup)]

    assert len(questions) == 3
    assert len(groups) == 2

    # Check specific question attributes
    select_q = next(q for q in questions if q.type == "select_multiple")
    assert len(select_q.choices) == 3
    assert select_q.allow_other is True

    range_q = next(q for q in questions if q.type == "range")
    assert range_q.range.start == 18
    assert range_q.range.end == 100

    # Check group attributes
    repeat_group = next(g for g in groups if g.type == "repeat")
    assert repeat_group.repeat_count == 3
    assert len(repeat_group.items) == 2
