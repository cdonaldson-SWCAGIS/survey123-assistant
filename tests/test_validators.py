"""Tests for XLSForm ORM validators."""
import pytest

from xlsform_orm.validators import (
    validate_name,
    validate_by_type,
    check_appearance_attributes,
    check_appearance_question_combo,
)
from xlsform_orm import QuestionTypes, AppearanceAttributes


def test_validate_name():
    """Test name validation against reserved keywords."""
    # Valid names should pass through unchanged
    assert validate_name("valid_name") == "valid_name"
    assert validate_name("question1") == "question1"
    assert validate_name("my_question") == "my_question"

    # Reserved keywords should raise ValueError
    with pytest.raises(ValueError):
        validate_name("SELECT")
    with pytest.raises(ValueError):
        validate_name("FROM")
    with pytest.raises(ValueError):
        validate_name("WHERE")


def test_validate_by_type():
    """Test type-specific validation rules."""
    # Test calculate type validation
    values = {
        "type": "calculate",
        "calculation": "1 + 1",
        "choices": None,
        "allow_other": None,
        "accuracyThreshold": None,
        "file": None,
        "range": None,
        "parameters": None,
    }
    result = validate_by_type(None, values)
    assert result["calculation"] == "1 + 1"

    # Test missing calculation
    values["calculation"] = None
    with pytest.raises(ValueError):
        validate_by_type(None, values)

    # Test select_one validation
    values = {
        "type": "select_one",
        "calculation": None,
        "choices": [{"value": "1", "label": "One"}],
        "allow_other": False,
        "accuracyThreshold": None,
        "file": None,
        "range": None,
        "parameters": None,
    }
    result = validate_by_type(None, values)
    assert result["choices"] == [{"value": "1", "label": "One"}]

    # Test missing choices
    values["choices"] = None
    with pytest.raises(ValueError):
        validate_by_type(None, values)


def test_check_appearance_attributes():
    """Test appearance attribute validation."""
    # Valid combinations
    values = {"type": "text", "appearance_attributes": "multiline"}
    assert check_appearance_attributes("multiline", values) == "multiline"

    values = {"type": "select_one", "appearance_attributes": "minimal"}
    assert check_appearance_attributes("minimal", values) == "minimal"

    # Invalid combinations
    values = {"type": "text", "appearance_attributes": "minimal"}
    with pytest.raises(ValueError):
        check_appearance_attributes("minimal", values)

    values = {"type": "select_one", "appearance_attributes": "multiline"}
    with pytest.raises(ValueError):
        check_appearance_attributes("multiline", values)


def test_check_appearance_question_combo():
    """Test appearance-question combination validation."""
    # Test valid combinations
    assert check_appearance_question_combo("multiline", "text")
    assert check_appearance_question_combo("minimal", "select_one")
    assert check_appearance_question_combo("horizontal", "select_multiple")
    assert check_appearance_question_combo("signature", "image")
    assert check_appearance_question_combo("year", "date")
    assert check_appearance_question_combo("numbers", "integer")

    # Test invalid combinations
    assert not check_appearance_question_combo("multiline", "select_one")
    assert not check_appearance_question_combo("minimal", "text")
    assert not check_appearance_question_combo("signature", "text")
    assert not check_appearance_question_combo("year", "text")


def test_validate_by_type_geo_questions():
    """Test validation for geo questions."""
    # Test geopoint validation
    values = {
        "type": "geopoint",
        "calculation": None,
        "choices": None,
        "allow_other": None,
        "accuracyThreshold": 5.0,
        "file": None,
        "range": None,
        "parameters": None,
    }
    result = validate_by_type(None, values)
    assert result["accuracyThreshold"] == 5.0

    # Test geotrace validation
    values["type"] = "geotrace"
    result = validate_by_type(None, values)
    assert result["accuracyThreshold"] == 5.0

    # Test geoshape validation
    values["type"] = "geoshape"
    result = validate_by_type(None, values)
    assert result["accuracyThreshold"] == 5.0


def test_validate_by_type_file_questions():
    """Test validation for file-based questions."""
    # Test select_one_from_file validation
    values = {
        "type": "select_one_from_file",
        "calculation": None,
        "choices": None,
        "allow_other": None,
        "accuracyThreshold": None,
        "file": "choices.csv",
        "range": None,
        "parameters": None,
    }
    result = validate_by_type(None, values)
    assert result["file"] == "choices.csv"

    # Test missing file
    values["file"] = None
    with pytest.raises(ValueError):
        validate_by_type(None, values)

    # Test select_multiple_from_file validation
    values["type"] = "select_multiple_from_file"
    values["file"] = "choices.csv"
    result = validate_by_type(None, values)
    assert result["file"] == "choices.csv"


def test_validate_by_type_range_question():
    """Test validation for range questions."""
    # Test valid range
    values = {
        "type": "range",
        "calculation": None,
        "choices": None,
        "allow_other": None,
        "accuracyThreshold": None,
        "file": None,
        "range": {"start": 0, "end": 100, "step": 5},
        "parameters": {},
    }
    result = validate_by_type(None, values)
    assert result["parameters"] == {"start": 0, "end": 100, "step": 5}

    # Test missing range
    values["range"] = None
    with pytest.raises(ValueError):
        validate_by_type(None, values)


def test_validate_by_type_clears_unused_fields():
    """Test that validator clears fields not used by the question type."""
    values = {
        "type": "text",
        "calculation": "should be cleared",
        "choices": ["should be cleared"],
        "allow_other": True,
        "accuracyThreshold": 5.0,
        "file": "should be cleared",
        "range": {"start": 0, "end": 100, "step": 5},
        "parameters": {"should": "be kept"},
    }
    result = validate_by_type(None, values)
    assert result["calculation"] is None
    assert result["choices"] is None
    assert result["allow_other"] is None
    assert result["accuracyThreshold"] is None
    assert result["file"] is None
    assert result["range"] is None
    assert result["parameters"] == {"should": "be kept"}
