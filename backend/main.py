"""FastAPI application entry point for the exam analysis tool."""

import sys
import os

# Ensure the backend directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import analysis, export

app = FastAPI(
    title="行政書士過去問分析ツール",
    description="行政書士試験の過去問出題傾向を分析・可視化するAPI",
    version="1.0.0",
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    """Initialize database on startup."""
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": "行政書士過去問分析ツール"}


# Register routers
app.include_router(analysis.router)
app.include_router(export.router)
