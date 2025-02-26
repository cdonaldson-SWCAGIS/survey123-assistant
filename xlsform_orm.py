"""Lightweight library supporting XLSForm-as-code."""
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
import yaml
from pydantic import BaseModel, Field, model_validator, field_validator


class LogicTypes(Enum):
    """Valid logic types."""
    trigger = "trigger"
    skip = "skip"
    relevant = "relevant"
    constraint = "constraint"


class Logic(BaseModel):
    """Logic for flow control and constraints."""
    type: Union[LogicTypes, str] = Field(..., description="logic type")
    expression: str = Field(..., description="logic expression")
    message: Optional[str] = Field(None, description="constraint message")

    class Config:
        """pydantic configuration."""
        use_enum_values = True

    @field_validator("message")
    def validate_message(cls, v, info):
        """Set message to None unless type == 'constraint'."""
        if info.data["type"] != "constraint":
            v = None
        return v


class Choice(BaseModel):
    """An individual choice for a rank or multiple choice question."""
    value: str = Field(..., description="The value of the choice")
    label: str = Field(..., description="The label of the choice")


class Range(BaseModel):
    """A value range for a range question."""
    start: Union[int, float] = Field(..., description="the value at which the range begins")
    end: Union[int, float] = Field(..., description="the value at which the range ends")
    step: Union[int, float] = Field(..., description="the size of each division in the range")


class GroupTypes(Enum):
    """Valid group types."""
    group = "group"
    repeat = "repeat"


class QuestionTypes(Enum):
    """Valid question types."""
    text = "text"
    integer = "integer"
    decimal = "decimal"
    date = "date"
    time = "time"
    dateTime = "dateTime"
    select_one = "select_one"
    select_multiple = "select_multiple"
    select_one_from_file = "select_one_from_file"
    select_multiple_from_file = "select_multiple_from_file"
    rank = "rank"
    range = "range"
    note = "note"
    geopoint = "geopoint"
    geotrace = "geotrace"
    geoshape = "geoshape"
    image = "image"
    audio = "audio"
    file = "file"
    barcode = "barcode"
    begin = "begin"
    end = "end"
    calculate = "calculate"
    hidden = "hidden"
    username = "username"
    email = "email"
    start = "start"
    deviceid = "deviceid"


class AppearanceAttributes(Enum):
    """Valid appearance attributes."""
    multiline = "multiline"
    minimal = "minimal"
    quick = "quick"
    no_calendar = "no-calendar"
    month_year = "month-year"
    year = "year"
    horizontal_compact = "horizontal-compact"
    horizontal = "horizontal"
    likert = "likert"
    compact = "compact"
    quickcompact = "quickcompact"
    field_list = "field-list"
    label = "label"
    list_nolabel = "list-nolabel"
    table_list = "table-list"
    signature = "signature"
    draw = "draw"
    map = "map"
    quick_map = "quick map"
    minimal_compact = "minimal compact"
    image_map = "image-map"
    autocomplete = "autocomplete"
    predictivetext = "predictivetext"
    nopredictivetext = "nopredictivetext"
    week_number = "week-number"
    distress = "distress"
    spinner = "spinner"
    numbers = "numbers"
    calculator = "calculator"
    thousands_sep = "thousands-sep"
    no_ticks = "no-ticks"
    annotate = "annotate"
    new_rear = "new-rear"
    new_front = "new-front"
    hidden = "hidden"
    geocode = "geocode"
    hide_input = "hide-input"
    press_to_locate = "press-to-locate"
    spike = "spike"
    spike_full_measure = "spike-full-measure"
    spike_point_to_point = "spike-point-to-point"


class Question(BaseModel):
    """A question of any type supported by XLSForm."""
    type: Union[QuestionTypes, str] = Field(..., description="xlsform question type")
    name: str = Field(..., description="question name")
    label: str = Field(..., description="question label")
    required: Optional[bool] = Field(None, description="True if question must be answered")
    default: Optional[str] = Field(None, description="default answer to question")
    hint: Optional[str] = Field(None, description="hint text shown for this question")
    logics: Optional[List[Logic]] = Field(None, description="question-level logic")

    # calculate
    calculation: Optional[str] = Field(None, description="expression used in calculation")

    # range
    range: Optional[Union[Range, Dict[str, Union[int, float]]]] = Field(
        None,
        description="parameters for range questions",
    )

    # geopoint, geotrace, geoshape
    accuracyThreshold: Optional[float] = Field(
        None,
        description="accuracy threshold used by geo questions",
    )

    # select_one, select_multiple
    choices: Optional[List[Choice]] = Field(
        None,
        description="choices for multiple choice and rank questions",
    )
    allow_other: Optional[bool] = Field(
        None,
        description="True if Other should be an option for multiple choice questions",
    )
    # select_one_from_file, select_multiple_from_file
    file: Optional[str] = Field(
        None,
        description="file used by questions with choices from file",
    )

    parameters: Optional[dict] = Field(
        None,
        description="parameter dict, specific to different question types",
    )
    appearance_attributes: Optional[Union[AppearanceAttributes, str]] = Field(
        None,
        description="question-level appearance attributes or grid theme format (w#:# or w#)",
    )
    parent_appearance: Optional[str] = Field(
        None,
        description="parent group's appearance attribute, used for grid theme validation",
    )

    class Config:
        """pydantic configuration."""
        use_enum_values = True

    @field_validator("name")
    def validate_name(cls, v):
        """Validate question name."""
        if v in RESERVED_NAMES:
            raise ValueError(f"{v} cannot be used as a question name")
        return v

    @model_validator(mode='after')
    def validate_by_type(cls, model):
        """Validate by question type."""
        values = model.model_dump()
        type = values["type"]

        if not hasattr(QuestionTypes, type):
            raise ValueError("Invalid question type")

        def check_associated(
            q_type: Union[str, Tuple[str, ...]],
            associated_field: str,
            required: bool = True,
        ):
            """Check for None if required; set None if unnecessary."""
            q_type = (q_type,) if isinstance(q_type, str) else q_type
            if type in q_type:
                if required and values[associated_field] is None:
                    raise ValueError(
                        f"{associated_field} required for type '{type}'",
                    )
            else:
                setattr(model, associated_field, None)

        check_associated("calculate", "calculation")
        check_associated(("rank", "select_one", "select_multiple"), "choices")
        check_associated(
            ("rank", "select_one", "select_multiple"),
            "allow_other",
            required=False,
        )
        check_associated(
            ("geopoint", "geotrace", "geoshape"),
            "accuracyThreshold",
            required=False,
        )
        check_associated(("select_one_from_file", "select_multiple_from_file"), "file")

        if type == "range":
            range_params = values["range"]
            if range_params is None:
                raise ValueError("range cannot be None when type == 'range'")
            parameters = values["parameters"] or {}
            parameters["start"] = range_params.start
            parameters["end"] = range_params.end
            parameters["step"] = range_params.step
            model.parameters = parameters

        return model

    @field_validator("appearance_attributes")
    def check_appearance_attributes(cls, v, info):
        """Validate appearance attributes."""
        if v is None:
            return v
        if isinstance(v, str) and v.startswith('w'):
            return v
        type = info.data.get("type")
        if not check_appearance_question_combo(v, type):
            raise ValueError(f"Appearance '{v}' is not compatible with question type '{type}'")
        return v


class QuestionGroup(BaseModel):
    """A group of questions or subgroups."""
    type: str = Field(GroupTypes.group, description="xlsform entry type")
    name: str = Field(..., description="name of the group")
    label: str = Field(..., description="label of the group")
    items: List[Union[Question, "QuestionGroup"]] = Field([], description="group items")
    logics: Optional[List[Logic]] = Field(None, description="group-level logic")
    repeat_count: Optional[Union[int, str]] = Field(None, description="number of repeats")
    appearance_attributes: Optional[Union[AppearanceAttributes, str]] = Field(
        None,
        description="group-level appearance attributes or grid theme format (w#:# or w#)",
    )
    parent_appearance: Optional[str] = Field(
        None,
        description="parent group's appearance attribute, used for grid theme validation",
    )

    class Config:
        """pydantic configuration."""
        use_enum_values = True

    @model_validator(mode='after')
    def validate_repeat(cls, model):
        """Set type to repeat_count or raise ValueError."""
        group_type = model.type

        if not hasattr(GroupTypes, group_type):
            raise ValueError("Invalid question type")

        repeat_count = model.repeat_count
        if group_type == "repeat":
            if repeat_count is None:
                raise ValueError("repeat_count cannot be None when type == 'repeat'")
        else:
            if repeat_count is not None:
                model.type = GroupTypes.repeat

        # Propagate appearance to items for grid theme validation
        items = model.items
        appearance = model.appearance_attributes
        if appearance and isinstance(appearance, str) and appearance.startswith('w'):
            for item in items:
                if not hasattr(item, "parent_appearance"):
                    continue
                item.parent_appearance = appearance

        return model

    @field_validator("appearance_attributes")
    def check_appearance_attributes(cls, v, info):
        """Validate appearance attributes."""
        if v is None:
            return v
        if isinstance(v, str) and v.startswith('w'):
            return v
        type = info.data.get("type")
        if not check_appearance_question_combo(v, type):
            raise ValueError(f"Appearance '{v}' is not compatible with question type '{type}'")
        return v


base_appearance_combos = (
    ("minimal", "select_one"),
    ("minimal", "select_multiple"),
    ("minimal", "barcode"),
    ("minimal", "begin"),
    ("minimal_compact", "begin"),
    ("compact", "select_one"),
    ("compact", "select_multiple"),
    ("compact", "begin"),
    ("horizontal", "select_one"),
    ("horizontal", "select_multiple"),
    ("horizontal_compact", "select_one"),
    ("horizontal_compact", "select_multiple"),
    ("image_map", "select_one"),
    ("image_map", "select_multiple"),
    ("autocomplete", "select_one"),
    ("likert", "select_one"),
    ("multiline", "text"),
    ("multiline", "image"),
    ("multiline", "file"),
    ("predictivetext", "text"),
    ("nopredictivetext", "text"),
    ("year", "date"),
    ("month_year", "date"),
    ("week_number", "date"),
    ("distress", "integer"),
    ("spinner", "integer"),
    ("spinner", "decimal"),
    ("numbers", "integer"),
    ("numbers", "decimal"),
    ("calculator", "integer"),
    ("calculator", "decimal"),
    ("thousands_sep", "decimal"),
    ("no_ticks", "range"),
    ("draw", "image"),
    ("annotate", "image"),
    ("signature", "image"),
    ("new_rear", "image"),
    ("new_front", "image"),
    ("field_list", "begin"),
    ("table_list", "begin"),
    ("geocode", "text"),
    ("hide_input", "geopoint"),
    ("press_to_locate", "geopoint"),
    ("press_to_locate", "geotrace"),
    ("press_to_locate", "geoshape"),
    ("spike", "image"),
    ("spike_full_measure", "image"),
    ("spike_point_to_point", "image"),
)
hidden_appearance_combos = tuple(("hidden", type.value) for type in QuestionTypes)
Appearance_Question_Combos = base_appearance_combos + hidden_appearance_combos


def check_appearance_question_combo(
    appearance_attribute: str,
    type: str,
) -> bool:
    """Check validity of appearance attribute for question type."""
    if isinstance(appearance_attribute, str) and appearance_attribute.startswith('w'):
        return True
    return (appearance_attribute, type) in Appearance_Question_Combos


RESERVED_NAMES = [
    # ... (keep the existing RESERVED_NAMES list)
]


def items_to_dfs(
    items: List[Union[QuestionGroup, Question]],
) -> Dict[str, pd.DataFrame]:
    """Convert a list of Questions and QuestionGroups into two DataFrames."""
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
    """Perform transformations on data as needed for XLSForm parsing."""
    return (
        df.fillna("")
        .astype(str)
        .replace({"[]": "", "{}": ""}, regex=False)
        .replace({"": None, True: "yes", False: "no"}, regex=False)
        .dropna(axis=1, how="all")
    )


def get_survey_args(excel_filepath: str) -> dict:
    """Return Survey-parseable dict from Excel file."""

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


class Survey(BaseModel):
    """A Pydantic model representing an XLSForm survey."""
    name: str = Field(..., description="name of the survey")
    label: str = Field(..., description="label of the survey")
    items: List[Union[Question, QuestionGroup]] = Field([], description="the survey's items")

    def get_dfs(self) -> Dict[str, pd.DataFrame]:
        """Return sheet_name: df dict for survey data."""
        settings_df = pd.DataFrame([{"form_id": self.name, "form_title": self.label}])
        df_dict = items_to_dfs(self.items)
        df_dict.update({"settings": settings_df})
        df_dict = {sheet_name: prep_for_excel(df) for sheet_name, df in df_dict.items()}
        return df_dict

    def save_to_excel(self, excel_filepath: str) -> None:
        """Save the survey data to an Excel file."""
        with pd.ExcelWriter(excel_filepath) as writer:
            for sheet_name, df in self.get_dfs().items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    @classmethod
    def parse_excel(cls, excel_filepath: str) -> "Survey":
        """Return Survey object based on Excel file."""
        survey_args = get_survey_args(excel_filepath)
        return cls.parse_obj(survey_args)

    def yaml(self) -> str:
        """Return yaml representation of self as str."""
        return yaml.dump(
            self.dict(exclude_none=True),
            default_flow_style=False,
            sort_keys=False,
        )

    @classmethod
    def parse_yaml(cls, yaml_str: str) -> "Survey":
        """Return Survey object given yaml str."""
        return cls(**yaml.safe_load(yaml_str))

    def save_to_yaml(self, yaml_filepath: str) -> None:
        """Save yaml representation of self to file."""
        with open(yaml_filepath, "w") as out_file:
            out_file.write(self.yaml())

    @classmethod
    def parse_yaml_file(cls, yaml_filepath: str) -> "Survey":
        """Return Survey object given yaml filepath."""
        with open(yaml_filepath) as in_file:
            yaml_str = in_file.read()
        return cls.parse_yaml(yaml_str)
