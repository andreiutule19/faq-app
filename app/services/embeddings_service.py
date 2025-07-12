import asyncio
import numpy as np
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from sqlalchemy.orm import Session
from app.models.database import FAQEntry, get_db
from app.core.config import settings
from app.core.celery_app import celery_app
import logging
from app.models.db import SessionLocal

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
    
    async def compute_embedding(self, text: str) -> List[float]:
        try:
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            raise
    
    async def compute_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            embeddings = await self.embeddings.aembed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"Error computing batch embeddings: {e}")
            raise

@celery_app.task
def compute_embeddings_for_collection(collection: str = "default"):
    
    db = SessionLocal()
    try:
        entries = db.query(FAQEntry).filter(
            FAQEntry.collection == collection,
            FAQEntry.embedding.is_(None)
        ).all()
        
        if not entries:
            logger.info(f"No entries to process for collection: {collection}")
            return
        
        embedding_service = EmbeddingService()
        questions = [entry.question for entry in entries]
        
        # Compute embeddings synchronously in the celery worker
        embeddings = asyncio.run(embedding_service.compute_embeddings_batch(questions))
        
        # Update entries with embeddings
        for entry, embedding in zip(entries, embeddings):
            entry.embedding = embedding
        
        db.commit()
        logger.info(f"Computed embeddings for {len(entries)} entries in collection: {collection}")
        
    except Exception as e:
        logger.error(f"Error computing embeddings for collection {collection}: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@celery_app.task
def update_embeddings_incremental(entry_ids: List[int]):
    db = SessionLocal()
    try:
        entries = db.query(FAQEntry).filter(FAQEntry.id.in_(entry_ids)).all()
        
        if not entries:
            logger.info("No entries to update")
            return
        
        embedding_service = EmbeddingService()
        questions = [entry.question for entry in entries]
        
        embeddings = asyncio.run(embedding_service.compute_embeddings_batch(questions))
        
        for entry, embedding in zip(entries, embeddings):
            entry.embedding = embedding
        
        db.commit()
        logger.info(f"Updated embeddings for {len(entries)} entries")
        
    except Exception as e:
        logger.error(f"Error updating embeddings: {e}")
        db.rollback()
        raise
    finally:
        db.close()