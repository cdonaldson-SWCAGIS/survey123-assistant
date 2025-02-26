"""Request and response handlers for Survey123 Assistant."""

import os
import tempfile
from typing import Dict, List, Optional, Tuple, Union

import pandas as pd
from pydantic import BaseModel

# Use relative import from the package
from xlsform_orm import Survey, Question, QuestionGroup, Choice, QuestionTypes


class SurveyRequest(BaseModel):
    """A request to create or modify a survey."""

    action: str
    survey_name: Optional[str] = None
    survey_label: Optional[str] = None
    questions: Optional[List[Dict]] = None
    groups: Optional[List[Dict]] = None
    file_path: Optional[str] = None


class SurveyResponse(BaseModel):
    """Response containing survey operation results."""

    success: bool
    message: str
    survey: Optional[Survey] = None
    file_path: Optional[str] = None
    error: Optional[str] = None


class RequestHandler:
    """Handles survey creation and modification requests."""

    @staticmethod
    def create_survey(request: SurveyRequest) -> SurveyResponse:
        """
        Create a new survey from the request.

        Parameters
        ----------
        request : SurveyRequest
            The survey creation request.

        Returns
        -------
        SurveyResponse
            The result of the survey creation operation.
        """
        try:
            # Create questions
            items = []
            if request.questions:
                for q_data in request.questions:
                    question = RequestHandler._create_question(q_data)
                    items.append(question)

            # Create groups
            if request.groups:
                for g_data in request.groups:
                    group = RequestHandler._create_group(g_data)
                    items.append(group)

            # Create survey
            survey = Survey(
                name=request.survey_name or "new_survey",
                label=request.survey_label or "New Survey",
                items=items,
            )

            # Save to file if path provided
            if request.file_path:
                if request.file_path.endswith(".xlsx"):
                    survey.save_to_excel(request.file_path)
                elif request.file_path.endswith(".yaml"):
                    survey.save_to_yaml(request.file_path)

            return SurveyResponse(
                success=True,
                message="Survey created successfully",
                survey=survey,
                file_path=request.file_path,
            )

        except Exception as e:
            return SurveyResponse(
                success=False,
                message="Failed to create survey",
                error=str(e),
            )

    @staticmethod
    def modify_survey(request: SurveyRequest) -> SurveyResponse:
        """
        Modify an existing survey.

        Parameters
        ----------
        request : SurveyRequest
            The survey modification request.

        Returns
        -------
        SurveyResponse
            The result of the survey modification operation.
        """
        try:
            # Load existing survey
            if not request.file_path:
                raise ValueError("File path required for survey modification")

            if request.file_path.endswith(".xlsx"):
                survey = Survey.parse_excel(request.file_path)
            elif request.file_path.endswith(".yaml"):
                survey = Survey.parse_yaml_file(request.file_path)
            else:
                raise ValueError("Unsupported file format")

            # Update survey attributes
            if request.survey_name:
                survey.name = request.survey_name
            if request.survey_label:
                survey.label = request.survey_label

            # Add new questions
            if request.questions:
                for q_data in request.questions:
                    question = RequestHandler._create_question(q_data)
                    survey.items.append(question)

            # Add new groups
            if request.groups:
                for g_data in request.groups:
                    group = RequestHandler._create_group(g_data)
                    survey.items.append(group)

            # Save modifications
            if request.file_path.endswith(".xlsx"):
                survey.save_to_excel(request.file_path)
            else:
                survey.save_to_yaml(request.file_path)

            return SurveyResponse(
                success=True,
                message="Survey modified successfully",
                survey=survey,
                file_path=request.file_path,
            )

        except Exception as e:
            return SurveyResponse(
                success=False,
                message="Failed to modify survey",
                error=str(e),
            )

    @staticmethod
    def _create_question(data: Dict) -> Question:
        """Create a Question object from dictionary data."""
        # Handle choices for select questions
        if data.get("choices"):
            choices = [
                Choice(value=c["value"], label=c["label"]) for c in data["choices"]
            ]
            data["choices"] = choices

        # Handle range parameters
        if data.get("range"):
            data["range"] = {
                k: float(v) if isinstance(v, str) else v
                for k, v in data["range"].items()
            }

        return Question(**data)

    @staticmethod
    def _create_group(data: Dict) -> QuestionGroup:
        """Create a QuestionGroup object from dictionary data."""
        # Create questions in the group
        if "items" in data:
            items = []
            for item_data in data["items"]:
                if item_data.get("type") in ("group", "repeat"):
                    item = RequestHandler._create_group(item_data)
                else:
                    item = RequestHandler._create_question(item_data)
                items.append(item)
            data["items"] = items

        return QuestionGroup(**data)


class FileHandler:
    """Handles file operations for surveys."""

    @staticmethod
    def save_survey(
        survey: Survey,
        format: str = "excel",
        directory: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Save a survey to file.

        Parameters
        ----------
        survey : Survey
            The survey to save.
        format : str
            The output format ('excel' or 'yaml').
        directory : Optional[str]
            Directory to save the file in. Uses temp directory if None.

        Returns
        -------
        Tuple[bool, str, Optional[str]]
            Success status, message, and file path if successful.
        """
        try:
            # Use provided directory or temp directory
            dir_path = directory or tempfile.gettempdir()
            os.makedirs(dir_path, exist_ok=True)

            # Generate file path
            file_name = f"{survey.name}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            if format == "excel":
                file_path = os.path.join(dir_path, f"{file_name}.xlsx")
                survey.save_to_excel(file_path)
            else:
                file_path = os.path.join(dir_path, f"{file_name}.yaml")
                survey.save_to_yaml(file_path)

            return True, "Survey saved successfully", file_path

        except Exception as e:
            return False, f"Failed to save survey: {str(e)}", None

    @staticmethod
    def load_survey(file_path: str) -> Tuple[bool, str, Optional[Survey]]:
        """
        Load a survey from file.

        Parameters
        ----------
        file_path : str
            Path to the survey file.

        Returns
        -------
        Tuple[bool, str, Optional[Survey]]
            Success status, message, and loaded survey if successful.
        """
        try:
            if file_path.endswith(".xlsx"):
                survey = Survey.parse_excel(file_path)
            elif file_path.endswith(".yaml"):
                survey = Survey.parse_yaml_file(file_path)
            else:
                raise ValueError("Unsupported file format")

            return True, "Survey loaded successfully", survey

        except Exception as e:
            return False, f"Failed to load survey: {str(e)}", None
