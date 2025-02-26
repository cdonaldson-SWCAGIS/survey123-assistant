"""OpenAI API integration for Survey123 Assistant."""

import os
from typing import Dict, List, Optional, Union

from openai import OpenAI
from pydantic import BaseModel


class Message(BaseModel):
    """A chat message."""

    role: str
    content: str
    file_ids: Optional[List[str]] = None


class AssistantResponse(BaseModel):
    """Response from the assistant."""

    messages: List[Message]
    file_ids: Optional[List[str]] = None
    output_content: Optional[str] = None


class AssistantAPI:
    """Handles OpenAI API interactions."""

    def __init__(self):
        """Initialize the API client."""
        self.client = OpenAI(
            organization=os.environ["OPENAI_ORG_ID"],
            api_key=os.environ["OPENAI_API_KEY"],
        )
        self.assistant = None
        self.thread = None
        self.file_id = None

    def initialize(self, instructions: str) -> None:
        """Initialize the assistant with instructions and file context."""
        if self.file_id is None:
            # Use the package module path instead of the root-level file
            import importlib.util
            import sys
            from pathlib import Path

            # Get the path to the xlsform_orm package
            xlsform_orm_spec = importlib.util.find_spec("xlsform_orm")
            if xlsform_orm_spec and xlsform_orm_spec.origin:
                package_path = Path(xlsform_orm_spec.origin).parent
                models_path = package_path / "models.py"

                if models_path.exists():
                    file = self.client.files.create(
                        file=open(models_path, "rb"),
                        purpose="assistants",
                    )
                    self.file_id = file.id
                else:
                    # Fallback to the root-level file if package path not found
                    file = self.client.files.create(
                        file=open("xlsform_orm.py", "rb"),
                        purpose="assistants",
                    )
                    self.file_id = file.id
            else:
                # Fallback to the root-level file if package not found
                file = self.client.files.create(
                    file=open("xlsform_orm.py", "rb"),
                    purpose="assistants",
                )
                self.file_id = file.id

        if self.assistant is None:
            self.assistant = self.client.beta.assistants.create(
                instructions=instructions,
                model="gpt-4-1106-preview",
                tools=[{"type": "code_interpreter"}],
                file_ids=[self.file_id],
            )

        if self.thread is None:
            self.thread = self.client.beta.threads.create()

    def send_message(self, content: str) -> AssistantResponse:
        """
        Send a message to the assistant and get the response.

        Parameters
        ----------
        content : str
            The message content to send.

        Returns
        -------
        AssistantResponse
            The assistant's response including messages and any file outputs.
        """
        # Add message to thread
        self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role="user",
            content=content,
        )

        # Run the assistant
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
        )

        # Wait for completion
        while run.status == "running":
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id,
            )

        if run.status == "failed":
            raise RuntimeError("Assistant run failed")

        # Get messages
        messages = self.client.beta.threads.messages.list(
            thread_id=self.thread.id,
        )

        # Convert to Message objects
        message_objects = []
        output_content = None
        file_ids = []

        for msg in messages:
            if msg.file_ids:
                file_ids.extend(msg.file_ids)
                # Get file content if available
                for file_id in msg.file_ids:
                    response = self.client.files.with_raw_response.retrieve_content(
                        file_id,
                    )
                    if response.status_code == 200:
                        output_content = response.content

            message_objects.append(
                Message(
                    role=msg.role,
                    content=msg.content[0].text.value,
                    file_ids=msg.file_ids,
                )
            )

        return AssistantResponse(
            messages=message_objects,
            file_ids=file_ids if file_ids else None,
            output_content=output_content,
        )

    def reset(self) -> None:
        """Reset the conversation thread."""
        if self.thread is not None:
            self.thread = self.client.beta.threads.create()
