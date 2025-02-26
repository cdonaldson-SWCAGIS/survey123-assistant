"""Tests for grid theme functionality."""

import pytest
from src.xlsform_orm.models import Question, QuestionGroup, Survey, QuestionTypes
from src.xlsform_orm.validators import (
    parse_grid_theme_appearance,
    validate_grid_theme_for_group,
)


def test_parse_grid_theme_appearance():
    """Test parsing of grid theme appearance parameter."""
    # Test valid formats
    assert parse_grid_theme_appearance("w4") == (4, 1)  # Default span is 1
    assert parse_grid_theme_appearance("w3:2") == (3, 2)
    assert parse_grid_theme_appearance("w10:5") == (10, 5)

    # Test invalid formats
    with pytest.raises(ValueError, match="Grid theme must start with 'w'"):
        parse_grid_theme_appearance("4:2")

    with pytest.raises(ValueError, match="Invalid grid theme format"):
        parse_grid_theme_appearance("w")

    with pytest.raises(ValueError, match="Invalid grid theme format"):
        parse_grid_theme_appearance("w:")

    with pytest.raises(ValueError, match="Invalid grid theme format"):
        parse_grid_theme_appearance("w:2")

    with pytest.raises(ValueError, match="Number of columns must be positive"):
        parse_grid_theme_appearance("w0:2")

    with pytest.raises(ValueError, match="Number of columns must be positive"):
        parse_grid_theme_appearance("w-1:2")

    with pytest.raises(ValueError, match="Span must be positive"):
        parse_grid_theme_appearance("w3:0")

    with pytest.raises(ValueError, match="Span must be positive"):
        parse_grid_theme_appearance("w3:-1")


def test_validate_grid_theme_for_group():
    """Test validation of grid theme parameters for groups."""
    # Test valid cases
    assert validate_grid_theme_for_group(4, 1) is True  # No parent
    assert validate_grid_theme_for_group(2, 2, parent_columns=4) is True  # With parent
    assert (
        validate_grid_theme_for_group(3, 3, parent_columns=3) is True
    )  # Equal to parent

    # Test invalid cases
    with pytest.raises(ValueError, match="Group span .* exceeds available columns"):
        validate_grid_theme_for_group(2, 5, parent_columns=4)


def test_question_grid_theme():
    """Test grid theme validation for questions."""
    # Test valid grid theme
    question = Question(
        type=QuestionTypes.TEXT,
        name="q1",
        label="Question 1",
        appearance_attributes="w2",
    )
    assert question.appearance_attributes == "w2"

    # Test invalid grid theme
    with pytest.raises(ValueError, match="Invalid grid theme format"):
        Question(
            type=QuestionTypes.TEXT,
            name="q2",
            label="Question 2",
            appearance_attributes="w",
        )


def test_group_grid_theme():
    """Test grid theme validation for groups."""
    # Test valid grid theme
    group = QuestionGroup(
        name="g1",
        label="Group 1",
        appearance_attributes="w4",
        items=[
            Question(
                type=QuestionTypes.TEXT,
                name="q1",
                label="Question 1",
                appearance_attributes="w2",
            ),
            Question(
                type=QuestionTypes.TEXT,
                name="q2",
                label="Question 2",
                appearance_attributes="w2",
            ),
        ],
    )
    assert group.appearance_attributes == "w4"
    assert group.items[0].parent_appearance == "w4"
    assert group.items[1].parent_appearance == "w4"

    # Test nested groups
    nested_group = QuestionGroup(
        name="parent",
        label="Parent Group",
        appearance_attributes="w6",
        items=[
            QuestionGroup(
                name="child",
                label="Child Group",
                appearance_attributes="w3:2",  # 3 columns, spans 2 columns of parent
                items=[
                    Question(
                        type=QuestionTypes.TEXT,
                        name="q1",
                        label="Question 1",
                        appearance_attributes="w1",
                    )
                ],
            )
        ],
    )
    assert nested_group.appearance_attributes == "w6"
    assert nested_group.items[0].appearance_attributes == "w3:2"
    assert nested_group.items[0].parent_appearance == "w6"

    # Test invalid nested group (span exceeds parent columns)
    with pytest.raises(ValueError) as excinfo:
        QuestionGroup(
            name="parent",
            label="Parent Group",
            appearance_attributes="w4",
            items=[
                QuestionGroup(
                    name="child",
                    label="Child Group",
                    appearance_attributes="w2:5",  # Invalid: spans 5 columns of parent's 4
                    items=[],
                )
            ],
        )
    assert "Group span" in str(excinfo.value) and "exceeds available columns" in str(
        excinfo.value
    )


def test_survey_grid_theme():
    """Test grid theme in a complete survey."""
    survey = Survey(
        name="test_survey",
        label="Test Survey",
        items=[
            QuestionGroup(
                name="contact_info",
                label="Contact Information",
                appearance_attributes="w2",  # 2-column grid
                items=[
                    Question(
                        type=QuestionTypes.TEXT,
                        name="first_name",
                        label="First Name",
                        appearance_attributes="w1",  # Takes 1 column
                    ),
                    Question(
                        type=QuestionTypes.TEXT,
                        name="last_name",
                        label="Last Name",
                        appearance_attributes="w1",  # Takes 1 column
                    ),
                    Question(
                        type=QuestionTypes.TEXT,
                        name="address",
                        label="Address",
                        appearance_attributes="w2",  # Takes full width (2 columns)
                    ),
                ],
            ),
            QuestionGroup(
                name="nested_example",
                label="Nested Grid Example",
                appearance_attributes="w6",  # 6-column grid
                items=[
                    QuestionGroup(
                        name="personal_info",
                        label="Personal Info",
                        appearance_attributes="w3:2",  # 3 columns, spans 2 columns of parent
                        items=[
                            Question(
                                type=QuestionTypes.TEXT,
                                name="age",
                                label="Age",
                                appearance_attributes="w1",
                            ),
                            Question(
                                type=QuestionTypes.TEXT,
                                name="gender",
                                label="Gender",
                                appearance_attributes="w2",
                            ),
                        ],
                    ),
                    QuestionGroup(
                        name="contact_details",
                        label="Contact Details",
                        appearance_attributes="w2:2",  # 2 columns, spans 2 columns of parent (fixed from 4)
                        items=[
                            Question(
                                type=QuestionTypes.TEXT,
                                name="email",
                                label="Email",
                                appearance_attributes="w1",
                            ),
                            Question(
                                type=QuestionTypes.TEXT,
                                name="phone",
                                label="Phone",
                                appearance_attributes="w1",
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )

    # Verify the structure was created successfully
    assert len(survey.items) == 2
    contact_info = survey.items[0]
    assert contact_info.appearance_attributes == "w2"
    assert len(contact_info.items) == 3
    assert (
        contact_info.items[2].appearance_attributes == "w2"
    )  # Address takes full width

    nested_example = survey.items[1]
    assert nested_example.appearance_attributes == "w6"
    assert len(nested_example.items) == 2
    assert nested_example.items[0].appearance_attributes == "w3:2"
    assert nested_example.items[1].appearance_attributes == "w2:2"  # Changed from w2:4
