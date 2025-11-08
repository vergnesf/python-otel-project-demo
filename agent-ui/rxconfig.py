"""
Reflex configuration
"""

import reflex as rx


config = rx.Config(
    app_name="agent_ui",
    frontend_port=3002,
    backend_port=8000,  # Port inside container (always 8000)
    # URL for browser to connect (outside container, port 8005)
    api_url="http://localhost:8005",
    # Disable sitemap plugin to remove warnings
    disable_plugins=["reflex.plugins.sitemap.SitemapPlugin"],
)
