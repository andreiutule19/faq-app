from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
from app.api.auth import create_access_token
from app.models.db import create_tables
from app.core.config import settings
import logging
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Semantic FAQ Assistant",
    description="AI-powered FAQ system with semantic search and OpenAI integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    create_tables()
    logger.info("Database tables created")


@app.post("/token")
async def login():
    """Simple token endpoint for testing authentication."""
    access_token = create_access_token(data={"sub": "test_user"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def root():
    return {"message": "Semantic FAQ Assistant API", "version": "1.0.0"}

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)