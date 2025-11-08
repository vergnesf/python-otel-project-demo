"""
FastAPI application for the Metrics Agent
"""

import logging
import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .metrics_analyzer import MetricsAnalyzer

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Metrics Agent API",
    description="Specialized agent for analyzing metrics from Mimir via MCP",
    version="0.1.0",
)

# Initialize analyzer
analyzer = MetricsAnalyzer()


class AnalyzeRequest(BaseModel):
    """Request to analyze metrics"""

    query: str
    time_range: str = "1h"
    context: dict = {}


class HealthResponse(BaseModel):
    """Health check response"""

    status: str
    mcp_server: str
    timestamp: datetime


@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    """
    Analyze metrics from Mimir based on user query
    
    Uses MCP Grafana server to query Mimir and provides intelligent analysis.
    """
    try:
        logger.info(f"Metrics agent received query: {request.query}")
        result = await analyzer.analyze(
            query=request.query,
            time_range=request.time_range,
            context=request.context,
        )
        logger.info(f"Metrics analysis completed")
        return result
    except Exception as e:
        logger.error(f"Metrics analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint
    
    Checks connectivity to MCP Grafana server.
    """
    mcp_status = await analyzer.check_mcp_health()
    
    return HealthResponse(
        status="healthy" if mcp_status else "unhealthy",
        mcp_server="reachable" if mcp_status else "unreachable",
        timestamp=datetime.now(),
    )


@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("Metrics Agent starting up...")
    logger.info(f"MCP Grafana URL: {os.getenv('MCP_GRAFANA_URL', 'http://grafana-mcp:8000')}")


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("Metrics Agent shutting down...")
    await analyzer.close()
