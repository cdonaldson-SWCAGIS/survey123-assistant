"""Shared test fixtures for XLSForm ORM."""

import pytest

from xlsform_orm import (
    Survey,
    Question,
    QuestionGroup,
    Choice,
    Range,
    Logic,
    QuestionTypes,
)


@pytest.fixture
def basic_question():
    """Return a basic text question."""
    return Question(
        type=QuestionTypes.text, name="text_question", label="What is your name?"
    )


@pytest.fixture
def choice_question():
    """Return a multiple choice question."""
    return Question(
        type=QuestionTypes.select_one,
        name="color_question",
        label="What is your favorite color?",
        choices=[
            Choice(value="r", label="Red"),
            Choice(value="b", label="Blue"),
            Choice(value="g", label="Green"),
        ],
    )


@pytest.fixture
def range_question():
    """Return a range question."""
    return Question(
        type=QuestionTypes.range,
        name="range_question",
        label="Number of individuals observed:",
        range=Range(start=0, end=100, step=5),
    )


@pytest.fixture
def question_group(basic_question, choice_question):
    """Return a question group."""
    return QuestionGroup(
        name="group1", label="Group 1", items=[basic_question, choice_question]
    )


@pytest.fixture
def repeat_group(basic_question):
    """Return a repeat group."""
    return QuestionGroup(
        name="repeat_group",
        label="Repeating group",
        type="repeat",
        repeat_count=3,
        items=[basic_question],
    )


@pytest.fixture
def survey_with_logic(basic_question, choice_question):
    """Return a survey with logic."""
    group = QuestionGroup(
        name="conditional_group",
        label="Conditional Questions",
        items=[choice_question],
        logics=[Logic(type="relevant", expression="${text_question} != ''")],
    )
    return Survey(
        name="logic_survey", label="Survey with Logic", items=[basic_question, group]
    )


@pytest.fixture
def complex_survey(
    basic_question, choice_question, range_question, question_group, repeat_group
):
    """Return a complex survey with various question types and groups."""
    return Survey(
        name="complex_survey",
        label="Complex Survey Example",
        items=[
            basic_question,
            question_group,
            Question(
                type=QuestionTypes.geopoint,
                name="location",
                label="Current location",
                accuracyThreshold=5.0,
            ),
            repeat_group,
            Question(
                type=QuestionTypes.calculate,
                name="total",
                label="Total value",
                calculation="sum(${range_question})",
            ),
        ],
    )
