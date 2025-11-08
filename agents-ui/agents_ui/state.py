"""
State management for the Agents UI
"""

import os
from typing import List

import httpx
import reflex as rx


class ChatState(rx.State):
    """
    State management for the chat interface
    """

    messages: List[dict] = []
    is_loading: bool = False

    async def send_message(self, form_data: dict):
        """
        Send a message to the orchestrator and get response
        
        Args:
            form_data: Form data containing the user query
        """
        query = form_data.get("query", "").strip()
        
        if not query:
            return
        
        # Add user message
        self.messages.append({
            "role": "user",
            "content": query,
        })
        
        # Set loading state
        self.is_loading = True
        
        try:
            # Call orchestrator
            orchestrator_url = os.getenv(
                "ORCHESTRATOR_URL",
                "http://agent-orchestrator:8001"
            )
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{orchestrator_url}/analyze",
                    json={
                        "query": query,
                        "time_range": "1h",
                    },
                )
                response.raise_for_status()
                result = response.json()
            
            # Format response
            formatted_response = self._format_response(result)
            
            # Add agent response
            self.messages.append({
                "role": "assistant",
                "content": formatted_response,
            })
        
        except Exception as e:
            # Add error message
            self.messages.append({
                "role": "assistant",
                "content": f"❌ Error: {str(e)}\n\nPlease check that all agents are running.",
            })
        
        finally:
            # Clear loading state
            self.is_loading = False

    def _format_response(self, result: dict) -> str:
        """
        Format the orchestrator response for display
        
        Args:
            result: Response from orchestrator
            
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Add summary
        lines.append("**Summary**")
        lines.append(result.get("summary", "No summary available"))
        lines.append("")
        
        # Add agent-specific responses
        agent_responses = result.get("agent_responses", {})
        
        if "logs" in agent_responses:
            logs = agent_responses["logs"]
            if "error" not in logs:
                lines.append("📜 **Logs Analysis**")
                lines.append(logs.get("analysis", "No logs analysis"))
                lines.append("")
        
        if "metrics" in agent_responses:
            metrics = agent_responses["metrics"]
            if "error" not in metrics:
                lines.append("📊 **Metrics Analysis**")
                lines.append(metrics.get("analysis", "No metrics analysis"))
                lines.append("")
        
        if "traces" in agent_responses:
            traces = agent_responses["traces"]
            if "error" not in traces:
                lines.append("🛤️ **Traces Analysis**")
                lines.append(traces.get("analysis", "No traces analysis"))
                lines.append("")
        
        # Add recommendations
        recommendations = result.get("recommendations", [])
        if recommendations:
            lines.append("💡 **Recommendations**")
            for i, rec in enumerate(recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Add Grafana link hint
        lines.append("📊 View detailed data in Grafana: http://localhost:3000")
        
        return "\n".join(lines)
