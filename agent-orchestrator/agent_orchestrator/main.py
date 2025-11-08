"""
FastAPI application for the Orchestrator Agent
"""

import logging
import os
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .orchestrator import Orchestrator

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Orchestrator Agent API",
    description="Main coordinator for observability agentic network",
    version="0.1.0",
)

# Initialize orchestrator
orchestrator = Orchestrator()


class AnalyzeRequest(BaseModel):
    """Request to analyze observability data"""

    query: str
    time_range: str = "1h"


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    agents: dict[str, str]
    timestamp: datetime


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Analyze observability issues based on user query

    Routes the query to specialized agents and synthesizes their responses.
    """
    try:
        logger.info(f"Received analysis request: {request.query}")
        result = await orchestrator.analyze(
            query=request.query,
            time_range=request.time_range,
        )
        logger.info(f"Analysis completed successfully")
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint

    Checks connectivity to all specialized agents.
    """
    agent_status = await orchestrator.check_agents_health()

    all_healthy = all(status == "reachable" for status in agent_status.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        agents=agent_status,
        timestamp=datetime.now(),
    )


@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("Orchestrator Agent starting up...")
    logger.info(
        f"Logs Agent URL: {os.getenv('AGENT_LOGS_URL', 'http://agent-logs:8002')}"
    )
    logger.info(
        f"Metrics Agent URL: {os.getenv('AGENT_METRICS_URL', 'http://agent-metrics:8003')}"
    )
    logger.info(
        f"Traces Agent URL: {os.getenv('AGENT_TRACES_URL', 'http://agent-traces:8004')}"
    )


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("Orchestrator Agent shutting down...")
    await orchestrator.close()
