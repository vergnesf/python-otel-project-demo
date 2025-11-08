"""
Main Reflex application for the Agents UI
"""

import reflex as rx

from .state import ChatState


def message_box(message: dict) -> rx.Component:
    """
    Render a single chat message

    Args:
        message: Message dictionary with 'role' and 'content'

    Returns:
        Reflex component for the message
    """
    is_user = message["role"] == "user"

    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(
                    "You" if is_user else "🤖 Agent",
                    font_weight="bold",
                    font_size="sm",
                    color="blue.600" if is_user else "purple.600",
                ),
                rx.text(
                    message["content"],
                    white_space="pre-wrap",
                    margin_top="2",
                ),
                padding="4",
                border_radius="lg",
                background_color="blue.50" if is_user else "purple.50",
                border=f"1px solid {'var(--blue-200)' if is_user else 'var(--purple-200)'}",
                width="100%",
            ),
            justify_content="flex-start" if not is_user else "flex-end",
            width="100%",
        ),
        margin_bottom="4",
        width="100%",
    )


def chat_interface() -> rx.Component:
    """
    Main chat interface component

    Returns:
        Reflex component for the chat UI
    """
    return rx.box(
        # Header
        rx.box(
            rx.heading(
                "🤖 Observability Agent Network",
                size="xl",
                margin_bottom="2",
            ),
            rx.text(
                "Ask questions about your microservices observability",
                color="gray.600",
                font_size="sm",
            ),
            padding="6",
            border_bottom="1px solid var(--gray-200)",
        ),
        # Chat messages
        rx.box(
            rx.foreach(
                ChatState.messages,
                message_box,
            ),
            rx.cond(
                ChatState.is_loading,
                rx.hstack(
                    rx.spinner(size="sm", color="purple.500"),
                    rx.text(
                        "Agents are analyzing...", color="gray.600", font_size="sm"
                    ),
                    padding="4",
                ),
            ),
            flex="1",
            overflow_y="auto",
            padding="6",
        ),
        # Input
        rx.box(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask about logs, metrics, or traces...",
                        name="query",
                        width="100%",
                        size="lg",
                        disabled=ChatState.is_loading,
                    ),
                    rx.button(
                        "Send",
                        type="submit",
                        size="lg",
                        color_scheme="purple",
                        disabled=ChatState.is_loading,
                    ),
                    spacing="2",
                    width="100%",
                ),
                on_submit=ChatState.send_message,
                width="100%",
            ),
            padding="6",
            border_top="1px solid var(--gray-200)",
        ),
        display="flex",
        flex_direction="column",
        height="100vh",
        max_width="1200px",
        margin="0 auto",
    )


def index() -> rx.Component:
    """
    Main page component

    Returns:
        Reflex component for the main page
    """
    return rx.container(
        chat_interface(),
        padding="0",
        max_width="100%",
    )


# Create the app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="purple",
    ),
)

# Add the index page
app.add_page(index, title="Observability Agents", route="/")
