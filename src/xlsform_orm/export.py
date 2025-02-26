"""Export functionality for XLSForm ORM."""
from typing import Any, Dict, Iterable, List, Union

import pandas as pd

from .models import Question, QuestionGroup, Choice


def items_to_dfs(
    items: List[Union[QuestionGroup, Question]],
) -> Dict[str, pd.DataFrame]:
    """
    Convert a list of Questions and QuestionGroups into two DataFrames.

    One DataFrame will contain the survey structure information,
    while the other will contain information on
    the choices available for multiple choice questions.

    Parameters
    ----------
    items : List[Union[QuestionGroup, Question]]
        A list of Questions and/or QuestionGroups to be converted to DataFrames.

    Returns
    -------
    A dictionary containing a survey df and a choices df.
    """
    survey_rows = []
    choices_rows = []
    if items is None:
        raise ValueError("items_to_df found no items")
    for item in items:
        item_dict = item.dict()
        type = item_dict["type"]

        if type in ("repeat", "group"):
            del item_dict["items"]
            item_dict.update({"type": f"begin {type}"})
            survey_rows.append(item_dict)
            _dfs = items_to_dfs(item.items)
            survey_rows += _dfs["survey"].to_dict("records")
            choices_rows += _dfs["choices"].to_dict("records")
            item_dict.update({"type": f"end {type}"})
            survey_rows.append(item_dict)

        elif type in ("rank", "select_one", "select_multiple"):
            list_name = item.name
            del item_dict["choices"]
            item_dict.update({"type": f"{type} {list_name}"})
            survey_rows.append(item_dict)
            if item.choices is not None:
                choices_rows += [
                    {
                        "list_name": list_name,
                        "name": choice.value,
                        "label": choice.label,
                    }
                    for choice in item.choices
                ]

        else:
            survey_rows.append(item_dict)

    survey_df = pd.DataFrame(survey_rows)
    choices_df = pd.DataFrame(choices_rows)

    return {"survey": survey_df, "choices": choices_df}


def prep_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform transformations on data as needed for XLSForm parsing.
    
    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to prepare for Excel export.
        
    Returns
    -------
    pd.DataFrame
        The prepared DataFrame.
    """
    return (
        df.fillna("")
        .astype(str)
        .replace({"[]": "", "{}": ""}, regex=False)
        .replace({"": None, True: "yes", False: "no"}, regex=False)
        .dropna(axis=1, how="all")
    )


def get_survey_args(excel_filepath: str) -> dict:
    """
    Return Survey-parseable dict from Excel file.
    
    Parameters
    ----------
    excel_filepath : str
        Path to the Excel file to parse.
        
    Returns
    -------
    dict
        A dictionary containing the survey arguments.
    """

    def link_choices(survey_row: dict, choice_dict: Dict[str, List[Choice]]) -> dict:
        """Link choices to questions."""
        type = survey_row["type"]
        type_with_choices = any(
            type.startswith(s)
            for s in (
                "rank",
                "select_one",
                "select_multiple",
            )
        )
        not_from_file = "from_file" not in type
        if type_with_choices and not_from_file:
            type_root, group_name = type.split()
            survey_row["type"] = type_root
            survey_row["choices"] = choice_dict.get(group_name, [])
        return survey_row

    def group_items(rows: Iterable[dict]):
        """Group items as appropriate, or not."""
        groups = []
        current_group = None
        for row in rows:
            type = row["type"]
            if type.startswith("begin"):
                group_type = type[6:]
                group_name = row["name"]
                current_group = QuestionGroup(
                    name=group_name,
                    type=group_type,
                    label=row.get("label", None),
                    items=[],
                )
                groups.append(current_group)
            elif type.startswith("end") and current_group is not None:
                current_group = None
            else:
                if current_group is not None:
                    current_group.items.append(Question.parse_obj(row))
                else:
                    groups.append(Question.parse_obj(row))
        return groups

    def drop_nan_dict(df: pd.DataFrame) -> List[dict]:
        """Return list of dicts with no nans."""
        return [
            {
                k: v
                for k, v in _dict.items()
                if not (isinstance(v, float) and pd.isna(v))
            }
            for _dict in (
                df.dropna(axis=0, how="all")
                .dropna(axis=1, how="all")
                .to_dict("records")
            )
        ]

    def get_choice_dict(choices_df: pd.DataFrame) -> Dict[str, List[Choice]]:
        """Return list_name: List[Choice] dict from choices_df."""
        return {
            list_name: [
                Choice.parse_obj(d)
                for d in drop_nan_dict(df.drop(columns=["list_name"]))
            ]
            for list_name, df in (
                choices_df.rename(columns={"name": "value"}).groupby(
                    "list_name",
                    as_index=False,
                )
            )
        }

    with pd.ExcelFile(excel_filepath) as xls:
        survey_df, choices_df, settings_df = (
            pd.read_excel(xls, sheet_name=sheet_name)
            for sheet_name in ("survey", "choices", "settings")
        )

    choice_dict: Dict[str, List[Choice]] = get_choice_dict(choices_df)
    items_grouped = group_items(
        link_choices(d, choice_dict) for d in drop_nan_dict(survey_df)
    )

    settings_dict = settings_df.iloc[0].to_dict()
    settings_dict.update(
        {
            "name": settings_dict["form_id"],
            "label": settings_dict["form_title"],
            "items": items_grouped,
        },
    )

    return settings_dict
