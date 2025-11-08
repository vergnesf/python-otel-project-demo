"""
Reflex configuration
"""

import reflex as rx


config = rx.Config(
    app_name="agents_ui",
    frontend_port=3002,
    backend_port=8000,
    api_url="http://0.0.0.0:8000",
)
