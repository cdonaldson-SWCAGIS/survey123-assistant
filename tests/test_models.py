"""Tests for XLSForm ORM models."""
import pytest
from pydantic import ValidationError

from xlsform_orm import (
    Survey,
    Question,
    QuestionGroup,
    Choice,
    Range,
    Logic,
    QuestionTypes,
    LogicTypes,
    GroupTypes,
)


def test_question_creation(basic_question):
    """Test basic question creation."""
    assert basic_question.type == QuestionTypes.text.value
    assert basic_question.name == "text_question"
    assert basic_question.label == "What is your name?"


def test_choice_question(choice_question):
    """Test multiple choice question creation and validation."""
    assert choice_question.type == QuestionTypes.select_one.value
    assert len(choice_question.choices) == 3
    assert choice_question.choices[0].value == "r"
    assert choice_question.choices[0].label == "Red"


def test_range_question(range_question):
    """Test range question creation and validation."""
    assert range_question.type == QuestionTypes.range.value
    assert range_question.range.start == 0
    assert range_question.range.end == 100
    assert range_question.range.step == 5


def test_question_group(question_group):
    """Test question group creation and validation."""
    assert question_group.type == GroupTypes.group.value
    assert len(question_group.items) == 2
    assert isinstance(question_group.items[0], Question)
    assert isinstance(question_group.items[1], Question)


def test_repeat_group(repeat_group):
    """Test repeat group creation and validation."""
    assert repeat_group.type == GroupTypes.repeat.value
    assert repeat_group.repeat_count == 3
    assert len(repeat_group.items) == 1


def test_survey_with_logic(survey_with_logic):
    """Test survey with logic creation and validation."""
    assert len(survey_with_logic.items) == 2
    group = survey_with_logic.items[1]
    assert isinstance(group, QuestionGroup)
    assert len(group.logics) == 1
    assert group.logics[0].type == LogicTypes.relevant.value
    assert group.logics[0].expression == "${text_question} != ''"


def test_complex_survey(complex_survey):
    """Test complex survey creation and validation."""
    assert len(complex_survey.items) == 5
    assert isinstance(complex_survey.items[0], Question)
    assert isinstance(complex_survey.items[1], QuestionGroup)
    assert isinstance(complex_survey.items[2], Question)
    assert isinstance(complex_survey.items[3], QuestionGroup)
    assert isinstance(complex_survey.items[4], Question)


def test_invalid_question_name():
    """Test that using a reserved keyword as question name raises ValidationError."""
    with pytest.raises(ValidationError):
        Question(
            type=QuestionTypes.text,
            name="SELECT",  # Reserved keyword
            label="Invalid question"
        )


def test_invalid_question_type():
    """Test that using an invalid question type raises ValidationError."""
    with pytest.raises(ValidationError):
        Question(
            type="invalid_type",
            name="test_question",
            label="Invalid question"
        )


def test_missing_required_fields():
    """Test that missing required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        Question(
            type=QuestionTypes.text,
            name="test_question"
            # Missing required 'label' field
        )


def test_invalid_range_values():
    """Test that invalid range values raise ValidationError."""
    with pytest.raises(ValidationError):
        Question(
            type=QuestionTypes.range,
            name="invalid_range",
            label="Invalid range",
            range=Range(start=100, end=0, step=5)  # Invalid: start > end
        )


def test_invalid_logic_type():
    """Test that invalid logic type raises ValidationError."""
    with pytest.raises(ValidationError):
        Logic(
            type="invalid_logic",
            expression="${q1} = 'yes'"
        )


def test_constraint_logic_requires_message():
    """Test that constraint logic requires a message."""
    with pytest.raises(ValidationError):
        Logic(
            type=LogicTypes.constraint,
            expression="${age} >= 18"
            # Missing required message for constraint type
        )


def test_repeat_group_requires_count():
    """Test that repeat group requires repeat_count."""
    with pytest.raises(ValidationError):
        QuestionGroup(
            name="invalid_repeat",
            label="Invalid Repeat Group",
            type=GroupTypes.repeat,
            items=[]
            # Missing required repeat_count
        )


def test_choice_validation():
    """Test choice validation."""
    with pytest.raises(ValidationError):
        Choice(
            value=""  # Empty value not allowed
            # Missing required label
        )


def test_survey_validation():
    """Test survey validation."""
    with pytest.raises(ValidationError):
        Survey(
            name="",  # Empty name not allowed
            label="Test Survey",
            items=[]
        )


def test_question_type_specific_validation():
    """Test validation specific to question types."""
    # Test calculate type requires calculation
    with pytest.raises(ValidationError):
        Question(
            type=QuestionTypes.calculate,
            name="calc",
            label="Calculate",
            # Missing required calculation
        )

    # Test geopoint type with accuracyThreshold
    question = Question(
        type=QuestionTypes.geopoint,
        name="location",
        label="Location",
        accuracyThreshold=5.0
    )
    assert question.accuracyThreshold == 5.0

    # Test select_one requires choices
    with pytest.raises(ValidationError):
        Question(
            type=QuestionTypes.select_one,
            name="choice",
            label="Choice",
            # Missing required choices
        )
