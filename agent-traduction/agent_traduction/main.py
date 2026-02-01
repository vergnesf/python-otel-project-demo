"""
FastAPI application for the Translation Agent
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .translation_service import TranslationService

log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

translator: TranslationService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global translator
    logger.info("Translation Agent starting up...")
    translator = TranslationService()
    yield
    logger.info("Translation Agent shutting down...")


app = FastAPI(
    lifespan=lifespan,
    title="Translation Agent API",
    description="Detects language and translates queries to English",
    version="0.1.0",
)


class TranslateRequest(BaseModel):
    """Translation request payload."""

    query: str
    model: str | None = None
    model_params: dict | None = None


class TranslateResponse(BaseModel):
    """Translation response payload."""

    agent_name: str
    language: str
    translated_query: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    llm: str
    timestamp: datetime


@app.post("/translate", response_model=TranslateResponse)
async def translate(request: TranslateRequest) -> TranslateResponse:
    """
    Detect language and translate the query to English when needed.
    """
    if not translator:
        raise HTTPException(status_code=503, detail="Translator not initialized")

    try:
        result = translator.translate(
            query=request.query,
            model=request.model,
            model_params=request.model_params,
        )
        return TranslateResponse(**result)
    except Exception as exc:
        logger.error("Translation failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Health check endpoint.
    """
    if not translator:
        return HealthResponse(
            status="unhealthy",
            llm="unavailable",
            timestamp=datetime.now(),
        )

    if translator.llm_ephemeral:
        llm_status = "ephemeral"
        status = "healthy"
    elif translator.llm:
        llm_status = "ready"
        status = "healthy"
    else:
        llm_status = "unavailable"
        status = "degraded"

    return HealthResponse(
        status=status,
        llm=llm_status,
        timestamp=datetime.now(),
    )
