"""
Main Reflex application for the Agents UI - Professional dark theme
"""

import reflex as rx

from .state import ChatState, QA


def message_content(text: str, is_user: bool = False) -> rx.Component:
    """Create a message content component.

    Args:
        text: The text to display.
        is_user: Whether this is a user message.

    Returns:
        A component displaying the message.
    """
    return rx.markdown(
        text,
        background_color="#2563EB" if is_user else "#1F2937",
        color="white",
        display="inline-block",
        padding="12px 16px",
        border_radius="12px",
    )


def message(qa: QA) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
    return rx.box(
        rx.box(
            message_content(qa.question, is_user=True),
            text_align="right",
            margin_bottom="12px",
        ),
        rx.cond(
            qa.answer != "",
            rx.box(
                message_content(qa.answer, is_user=False),
                text_align="left",
                margin_bottom="12px",
            ),
        ),
        max_width="50em",
        margin_inline="auto",
    )


def chat_area() -> rx.Component:
    """List all the messages in a single conversation."""
    return rx.auto_scroll(
        rx.foreach(ChatState.chats, message),
        flex="1",
        padding="16px",
        background_color="#0F172A",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.center(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask about your microservices...",
                        id="question",
                        flex="1",
                        background_color="#1F2937",
                        border="1px solid #374151",
                        color="white",
                        _placeholder={"color": "#9CA3AF"},
                        _focus={
                            "border_color": "#2563EB",
                            "outline": "none",
                        },
                    ),
                    rx.button(
                        "Send",
                        loading=ChatState.processing,
                        disabled=ChatState.processing,
                        type="submit",
                        background_color="#2563EB",
                        color="white",
                        _hover={
                            "background_color": "#1D4ED8",
                        },
                    ),
                    max_width="50em",
                    margin="0 auto",
                    align_items="center",
                    spacing="3",
                ),
                reset_on_submit=True,
                on_submit=ChatState.send_message,
            ),
            rx.text(
                "Observability Assistant - Ask questions about logs, metrics, and traces",
                text_align="center",
                font_size="14px",
                color="#6B7280",
            ),
            width="100%",
            padding_x="16px",
            align="stretch",
            spacing="2",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top="1px solid #1F2937",
        background_color="#111827",
        align="stretch",
        width="100%",
    )


def navbar() -> rx.Component:
    """Simple navbar with title."""
    return rx.hstack(
        rx.heading(
            "🔍 Observability Assistant",
            size="6",
            color="white",
        ),
        justify_content="center",
        align_items="center",
        padding="16px",
        border_bottom="1px solid #1F2937",
        background_color="#111827",
    )


def index() -> rx.Component:
    """The main app."""
    return rx.vstack(
        navbar(),
        chat_area(),
        action_bar(),
        background_color="#0F172A",
        color="white",
        height="100dvh",
        align_items="stretch",
        spacing="0",
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="dark",
        accent_color="blue",
    ),
)

app.add_page(index, title="Observability Assistant", route="/")
