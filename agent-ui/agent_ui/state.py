"""
State management for Agents UI
"""

import os
import reflex as rx
from typing import Any
from pydantic import BaseModel
import httpx


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

        # Call orchestrator API
        orchestrator_url = os.getenv(
            "ORCHESTRATOR_URL", "http://agent-orchestrator:8001"
        )

        # Detect time range in question (e.g., "5 dernières minutes")
        time_range = "1h"
        q_lower = question.lower()
        if "5" in q_lower and (
            "minute" in q_lower or "minutes" in q_lower or "5m" in q_lower
        ):
            time_range = "5m"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{orchestrator_url}/analyze",
                    json={"query": question, "time_range": time_range},
                )
                response.raise_for_status()
                result = response.json()

                # Format the response
                answer_parts = [f"**Summary:**\n{result['summary']}"]

                if result.get("recommendations"):
                    answer_parts.append("\n\n**Recommendations:**")
                    for rec in result["recommendations"]:
                        answer_parts.append(f"- {rec}")

                answer = "\n".join(answer_parts)

        except httpx.HTTPError as e:
            answer = f"❌ Error connecting to orchestrator: {str(e)}\n\nPlease ensure the orchestrator service is running."
        except Exception as e:
            answer = f"❌ Unexpected error: {str(e)}"

        self.chats[-1].answer = answer
        self.processing = False
        yield
