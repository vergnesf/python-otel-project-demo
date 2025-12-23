"""
FastAPI application for the Orchestrator Agent
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

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

# Initialize orchestrator (will be set in lifespan)
orchestrator: Orchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator
    # Startup
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
    orchestrator = Orchestrator()
    yield
    # Shutdown
    logger.info("Orchestrator Agent shutting down...")
    await orchestrator.close()


app = FastAPI(
    lifespan=lifespan,
    title="Orchestrator Agent API",
    description="Main coordinator for observability agentic network",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    """Request to analyze observability data"""

    query: str
    time_range: str = "1h"
    model: str | None = None


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
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    try:
        logger.info(f"Received analysis request: {request.query}")
        result = await orchestrator.analyze(
            query=request.query,
            time_range=request.time_range,
            model=request.model,
        )
        logger.info("Analysis completed successfully")
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
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")

    agent_status = await orchestrator.check_agents_health()

    all_healthy = all(status == "reachable" for status in agent_status.values())
    status = "healthy" if all_healthy else "degraded"

    return HealthResponse(
        status=status,
        agents=agent_status,
        timestamp=datetime.now(),
    )
