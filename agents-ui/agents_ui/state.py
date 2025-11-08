"""
State management for Agents UI
"""

import reflex as rx
from typing import Any
from pydantic import BaseModel


class QA(BaseModel):
    """A question and answer pair."""
    question: str
    answer: str = ""


class ChatState(rx.State):
    """The app state."""

    # List of chat messages
    chats: list[QA] = []

    # Whether we are processing the question
    processing: bool = False

    @rx.var
    def messages(self) -> list[dict]:
        """Get messages in the format expected by the UI.
        
        Returns:
            List of messages with role and content
        """
        result = []
        for qa in self.chats:
            result.append({"role": "user", "content": qa.question})
            if qa.answer:
                result.append({"role": "assistant", "content": qa.answer})
        return result

    @rx.var
    def is_loading(self) -> bool:
        """Check if we are currently processing.
        
        Returns:
            True if processing
        """
        return self.processing

    @rx.event
    async def send_message(self, form_data: dict[str, Any]):
        """Process a new message.
        
        Args:
            form_data: Form data containing the question
        """
        # Get the question from the form
        question = form_data.get("question", "")

        # Check if the question is empty
        if not question:
            return

        # Add the question to the chat
        qa = QA(question=question, answer="")
        self.chats.append(qa)

        # Start processing
        self.processing = True
        yield

        # TODO: Call orchestrator API here
        # For now, just echo back
        answer = f"You asked: {question}\n\nThis will be connected to the orchestrator API."
        
        self.chats[-1].answer = answer
        self.processing = False
        yield
