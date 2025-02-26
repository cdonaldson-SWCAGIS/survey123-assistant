"""Models for XLSForm ORM."""

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, validator

from .constants import QuestionTypes
from .validators import (
    check_appearance_attributes,
    parse_grid_theme_appearance,
    validate_grid_theme_for_group,
    validate_name,
)


class GroupTypes(str, Enum):
    """Group types supported by Survey123."""

    GROUP = "group"
    REPEAT = "repeat"


class LogicTypes(str, Enum):
    """Logic types supported by Survey123."""

    RELEVANT = "relevant"
    CONSTRAINT = "constraint"
    CALCULATION = "calculation"
    CHOICE_FILTER = "choice_filter"
    REQUIRED = "required"


class AppearanceAttributes(str, Enum):
    """Appearance attributes supported by Survey123."""

    MINIMAL = "minimal"
    MINIMAL_COMPACT = "minimal_compact"
    COMPACT = "compact"
    HORIZONTAL = "horizontal"
    HORIZONTAL_COMPACT = "horizontal_compact"
    IMAGE_MAP = "image_map"
    AUTOCOMPLETE = "autocomplete"
    LIKERT = "likert"
    MULTILINE = "multiline"
    PREDICTIVETEXT = "predictivetext"
    NOPREDICTIVETEXT = "nopredictivetext"
    YEAR = "year"
    MONTH_YEAR = "month_year"
    WEEK_NUMBER = "week_number"
    DISTRESS = "distress"
    SPINNER = "spinner"
    NUMBERS = "numbers"
    CALCULATOR = "calculator"
    THOUSANDS_SEP = "thousands_sep"
    NO_TICKS = "no_ticks"
    DRAW = "draw"
    ANNOTATE = "annotate"
    SIGNATURE = "signature"
    NEW_REAR = "new_rear"
    NEW_FRONT = "new_front"
    FIELD_LIST = "field_list"
    TABLE_LIST = "table_list"
    GEOCODE = "geocode"
    HIDE_INPUT = "hide_input"
    PRESS_TO_LOCATE = "press_to_locate"
    SPIKE = "spike"
    SPIKE_FULL_MEASURE = "spike_full_measure"
    SPIKE_POINT_TO_POINT = "spike_point_to_point"
    HIDDEN = "hidden"


class Range(BaseModel):
    """Range parameters for range questions."""

    start: Union[int, float]
    end: Union[int, float]
    step: Union[int, float]


class Logic(BaseModel):
    """Logic for questions and groups."""

    type: LogicTypes
    expression: str


class Choice(BaseModel):
    """Choice for select questions."""

    value: str
    label: str


class Question(BaseModel):
    """Question in a Survey123 form."""

    type: QuestionTypes
    name: str
    label: str
    hint: Optional[str] = None
    required: Optional[bool] = None
    read_only: Optional[bool] = None
    default: Optional[str] = None
    appearance_attributes: Optional[str] = None
    parent_appearance: Optional[str] = None
    parameters: Optional[dict] = None
    calculation: Optional[str] = None
    choices: Optional[List[Choice]] = None
    range: Optional[Range] = None
    file: Optional[str] = None
    allow_other: Optional[bool] = None
    accuracyThreshold: Optional[int] = None
    logic: Optional[List[Logic]] = None

    _validate_name = validator("name", allow_reuse=True)(validate_name)
    _validate_appearance = validator(
        "appearance_attributes", pre=True, allow_reuse=True
    )(check_appearance_attributes)

    @validator("appearance_attributes")
    def validate_grid_theme(cls, v, values):
        """Validate grid theme appearance attributes."""
        if v and v.startswith("w"):
            columns, _ = parse_grid_theme_appearance(v)
            if values.get("parent_appearance"):
                parent_columns, _ = parse_grid_theme_appearance(
                    values["parent_appearance"]
                )
                validate_grid_theme_for_group(columns, 1, parent_columns)
        return v


class QuestionGroup(BaseModel):
    """Group of questions in a Survey123 form."""

    name: str
    type: GroupTypes = GroupTypes.GROUP
    label: Optional[str] = None
    hint: Optional[str] = None
    required: Optional[bool] = None
    read_only: Optional[bool] = None
    appearance_attributes: Optional[str] = None
    parent_appearance: Optional[str] = None
    parameters: Optional[dict] = None
    repeat_count: Optional[int] = None
    logic: Optional[List[Logic]] = None
    items: List[Union["QuestionGroup", Question]] = []

    _validate_name = validator("name", allow_reuse=True)(validate_name)
    _validate_appearance = validator(
        "appearance_attributes", pre=True, allow_reuse=True
    )(check_appearance_attributes)

    @validator("appearance_attributes")
    def validate_grid_theme(cls, v, values):
        """Validate grid theme appearance attributes."""
        if v and v.startswith("w"):
            columns, span = parse_grid_theme_appearance(v)
            if values.get("parent_appearance"):
                parent_columns, _ = parse_grid_theme_appearance(
                    values["parent_appearance"]
                )
                validate_grid_theme_for_group(columns, span, parent_columns)
            # Always check if span exceeds available columns
            if ":" in v:
                _, span_value = v[1:].split(":")
                span = int(span_value)
                if span > columns:
                    raise ValueError(
                        f"Group span {span} exceeds available columns {columns}"
                    )
        return v

    def __init__(self, **data):
        """Initialize group and set parent appearance for items."""
        super().__init__(**data)
        if self.appearance_attributes and self.appearance_attributes.startswith("w"):
            for item in self.items:
                item.parent_appearance = self.appearance_attributes


class Survey(BaseModel):
    """Survey123 form."""

    name: str
    label: str
    description: Optional[str] = None
    version: Optional[str] = None
    instance_name: Optional[str] = None
    style: Optional[str] = None
    submission_url: Optional[str] = None
    default_language: Optional[str] = None
    languages: Optional[List[str]] = None
    public_key: Optional[str] = None
    auto_send: Optional[bool] = None
    auto_delete: Optional[bool] = None
    users: Optional[List[str]] = None
    groups: Optional[List[str]] = None
    items: List[Union[QuestionGroup, Question]] = []

    _validate_name = validator("name", allow_reuse=True)(validate_name)
