"""
Main FastAPI application for the Agents UI - Professional dark theme
"""

import logging
import os
from typing import List

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Setup logging
logger = logging.getLogger("agent_ui")

# Models
class QA(BaseModel):
    """A question and answer pair."""
    question: str
    answer: str = ""

class ChatState:
    """The app state."""

    def __init__(self):
        self.chats: List[QA] = []
        self.processing: bool = False

    def get_messages(self) -> List[dict]:
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

    def is_loading(self) -> bool:
        """Check if we are currently processing.

        Returns:
            True if processing
        """
        return self.processing

# Global state
chat_state = ChatState()

# FastAPI app with root_path for Traefik proxy (strips /agents/ui prefix)
root_path = os.getenv("ROOT_PATH", "")
app = FastAPI(title="Observability Assistant", root_path=root_path)

# Templates
templates = Jinja2Templates(directory="agent_ui/templates")

# Mount static files (if directory exists)
if os.path.exists("agent_ui/static"):
    app.mount("/static", StaticFiles(directory="agent_ui/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main chat interface."""
    logger.info("Rendering main page")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "chats": chat_state.chats,
            "processing": chat_state.processing,
            "root_path": root_path
        }
    )

@app.post("/send_message")
async def send_message(
    request: Request,
    question: str = Form(...)
):
    """Process a new message.

    Args:
        question: The question from the user
    """
    logger.info(f"Received question: {question[:50]}...")

    # Check if the question is empty
    if not question.strip():
        logger.warning("Empty question received")
        return {"status": "error", "message": "Question cannot be empty"}

    # Add the question to the chat
    qa = QA(question=question.strip(), answer="")
    chat_state.chats.append(qa)
    chat_state.processing = True
    logger.info("Processing question...")

    # Call orchestrator API
    orchestrator_url = os.getenv(
        "ORCHESTRATOR_URL", "http://agent-orchestrator:8001"
    )

    # Detect time range in question (e.g., "last 5 minutes")
    time_range = "1h"
    q_lower = question.lower()
    if "5" in q_lower and (
        "minute" in q_lower or "minutes" in q_lower or "5m" in q_lower
    ):
        time_range = "5m"

    try:
        # Orchestrator timeout should match agent call timeout to allow model loading (default 600s)
        orchestrator_timeout = int(os.getenv("ORCHESTRATOR_TIMEOUT", "600"))
        async with httpx.AsyncClient(timeout=orchestrator_timeout) as client:
            response = await client.post(
                f"{orchestrator_url}/analyze",
                json={"query": question, "time_range": time_range},
            )
            response.raise_for_status()
            result = response.json()

            # Format the response
            answer_parts = [result["summary"]]

            if result.get("recommendations"):
                answer_parts.append("\n\n**Recommendations:**")
                for rec in result["recommendations"]:
                    answer_parts.append(f"- {rec}")

            answer = "\n".join(answer_parts)

    except httpx.HTTPError as e:
        logger.error(f"Orchestrator connection error: {str(e)}")
        answer = f"❌ Error connecting to orchestrator: {str(e)}\n\nPlease ensure the orchestrator service is running."
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        answer = f"❌ Unexpected error: {str(e)}"

    # Update the answer
    chat_state.chats[-1].answer = answer
    chat_state.processing = False
    logger.info("Question processed successfully")

    return {"status": "success", "answer": answer}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "agent-ui"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Agent UI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
