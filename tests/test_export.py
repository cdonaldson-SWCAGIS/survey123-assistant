"""Tests for XLSForm ORM export functionality."""
import os
import tempfile

import pandas as pd
import pytest

from xlsform_orm.export import (
    items_to_dfs,
    prep_for_excel,
    get_survey_args,
)
from xlsform_orm import Survey, Question, QuestionGroup, Choice, QuestionTypes


def test_items_to_dfs_basic(basic_question):
    """Test basic conversion of items to DataFrames."""
    result = items_to_dfs([basic_question])
    
    # Check survey DataFrame
    assert "survey" in result
    assert len(result["survey"]) == 1
    assert result["survey"].iloc[0]["type"] == "text"
    assert result["survey"].iloc[0]["name"] == "text_question"
    
    # Check choices DataFrame (should be empty)
    assert "choices" in result
    assert len(result["choices"]) == 0


def test_items_to_dfs_choices(choice_question):
    """Test conversion of choice questions to DataFrames."""
    result = items_to_dfs([choice_question])
    
    # Check survey DataFrame
    assert len(result["survey"]) == 1
    assert result["survey"].iloc[0]["type"] == "select_one color_question"
    
    # Check choices DataFrame
    assert len(result["choices"]) == 3
    assert list(result["choices"]["list_name"].unique()) == ["color_question"]
    assert list(result["choices"]["value"]) == ["r", "b", "g"]
    assert list(result["choices"]["label"]) == ["Red", "Blue", "Green"]


def test_items_to_dfs_groups(question_group):
    """Test conversion of question groups to DataFrames."""
    result = items_to_dfs([question_group])
    
    # Check survey DataFrame structure
    assert len(result["survey"]) == 4  # begin group + 2 questions + end group
    assert result["survey"].iloc[0]["type"] == "begin group"
    assert result["survey"].iloc[-1]["type"] == "end group"
    
    # Check group content
    group_rows = result["survey"].to_dict("records")
    assert group_rows[0]["name"] == "group1"
    assert group_rows[1]["type"] == "text"
    assert group_rows[2]["type"].startswith("select_one")


def test_items_to_dfs_repeat_groups(repeat_group):
    """Test conversion of repeat groups to DataFrames."""
    result = items_to_dfs([repeat_group])
    
    # Check survey DataFrame structure
    assert len(result["survey"]) == 3  # begin repeat + question + end repeat
    assert result["survey"].iloc[0]["type"] == "begin repeat"
    assert result["survey"].iloc[-1]["type"] == "end repeat"
    
    # Check repeat group attributes
    first_row = result["survey"].iloc[0]
    assert first_row["name"] == "repeat_group"
    assert first_row["repeat_count"] == 3


def test_items_to_dfs_complex(complex_survey):
    """Test conversion of complex survey to DataFrames."""
    result = items_to_dfs(complex_survey.items)
    
    # Check overall structure
    assert "survey" in result
    assert "choices" in result
    
    # Verify all question types are present
    survey_types = result["survey"]["type"].tolist()
    assert "text" in survey_types
    assert any(t.startswith("select_one") for t in survey_types)
    assert "geopoint" in survey_types
    assert "calculate" in survey_types
    
    # Check group structure
    assert "begin group" in survey_types
    assert "end group" in survey_types
    assert "begin repeat" in survey_types
    assert "end repeat" in survey_types


def test_prep_for_excel():
    """Test DataFrame preparation for Excel export."""
    df = pd.DataFrame({
        "empty_list": [[]],
        "empty_dict": [{}],
        "none_value": [None],
        "bool_true": [True],
        "bool_false": [False],
        "normal_text": ["test"],
        "empty_column": [None, None],
    })
    
    result = prep_for_excel(df)
    
    # Check transformations
    assert result["empty_list"].iloc[0] == ""
    assert result["empty_dict"].iloc[0] == ""
    assert result["none_value"].iloc[0] is None
    assert result["bool_true"].iloc[0] == "yes"
    assert result["bool_false"].iloc[0] == "no"
    assert result["normal_text"].iloc[0] == "test"
    assert "empty_column" not in result.columns


def test_get_survey_args():
    """Test Excel to Survey args conversion."""
    # Create a temporary Excel file
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        # Create test survey
        survey = Survey(
            name="test_survey",
            label="Test Survey",
            items=[
                Question(
                    type=QuestionTypes.text,
                    name="q1",
                    label="Question 1"
                ),
                QuestionGroup(
                    name="group1",
                    label="Group 1",
                    items=[
                        Question(
                            type=QuestionTypes.select_one,
                            name="q2",
                            label="Question 2",
                            choices=[
                                Choice(value="a", label="Option A"),
                                Choice(value="b", label="Option B"),
                            ]
                        )
                    ]
                )
            ]
        )
        
        # Save to Excel
        survey.save_to_excel(tmp.name)
        
        # Test conversion back to survey args
        args = get_survey_args(tmp.name)
        
        # Verify structure
        assert args["name"] == "test_survey"
        assert args["label"] == "Test Survey"
        assert len(args["items"]) == 2
        
        # Check first question
        assert isinstance(args["items"][0], Question)
        assert args["items"][0].type == "text"
        assert args["items"][0].name == "q1"
        
        # Check group
        assert isinstance(args["items"][1], QuestionGroup)
        assert args["items"][1].name == "group1"
        assert len(args["items"][1].items) == 1
        
        # Check choice question in group
        choice_q = args["items"][1].items[0]
        assert choice_q.type == "select_one"
        assert len(choice_q.choices) == 2
        assert choice_q.choices[0].value == "a"
        assert choice_q.choices[1].label == "Option B"
    
    # Clean up
    os.unlink(tmp.name)


def test_items_to_dfs_empty():
    """Test handling of empty items list."""
    with pytest.raises(ValueError):
        items_to_dfs(None)

    result = items_to_dfs([])
    assert len(result["survey"]) == 0
    assert len(result["choices"]) == 0


def test_items_to_dfs_nested_groups(complex_survey):
    """Test handling of nested groups."""
    # Create a nested group structure
    nested_group = QuestionGroup(
        name="outer",
        label="Outer Group",
        items=[
            Question(
                type=QuestionTypes.text,
                name="q1",
                label="Q1"
            ),
            QuestionGroup(
                name="inner",
                label="Inner Group",
                items=[
                    Question(
                        type=QuestionTypes.text,
                        name="q2",
                        label="Q2"
                    )
                ]
            )
        ]
    )
    
    result = items_to_dfs([nested_group])
    
    # Check structure
    survey_types = result["survey"]["type"].tolist()
    assert survey_types == [
        "begin group",  # outer
        "text",        # q1
        "begin group", # inner
        "text",        # q2
        "end group",   # inner
        "end group"    # outer
    ]


def test_get_survey_args_invalid_file():
    """Test handling of invalid Excel file."""
    with pytest.raises(Exception):
        get_survey_args("nonexistent.xlsx")


def test_prep_for_excel_edge_cases():
    """Test prep_for_excel with edge cases."""
    df = pd.DataFrame({
        "mixed_none": [None, "text", None],
        "all_none": [None, None, None],
        "special_chars": ["test\n", "test\t", "test\r"],
        "numbers": [1, 2.5, 3],
    })
    
    result = prep_for_excel(df)
    
    # Check handling of None values
    assert result["mixed_none"].isna().sum() == 2
    assert "all_none" not in result.columns
    
    # Check type conversion
    assert result["numbers"].dtype == "object"
    assert all(isinstance(x, str) for x in result["numbers"])
    
    # Check special characters
    assert all(isinstance(x, str) for x in result["special_chars"])
