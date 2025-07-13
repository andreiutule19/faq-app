from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.models.db import create_tables
import logging
import uvicorn
from contextlib import asynccontextmanager


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FAQ app",
    description="AI-powered FAQ system with semantic search and OpenAI integration",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api/v1")


@asynccontextmanager
async def startup_event():
    create_tables()
    logger.info("Database tables created")


@app.get("/")
async def root():
    return {"message": "FAQ app", "version": "1.0.0"}

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)