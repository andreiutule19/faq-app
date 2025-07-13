import asyncio
import numpy as np
from typing import List, Optional
from langchain_openai import OpenAIEmbeddings
from app.models.db import FAQEntry
from app.core.settings import settings
from app.core.celery_app import celery_app
import logging
from app.models.db import SessionLocal
from app.core.rate_limiter import openai_rate_limiter
import openai

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.openai_api_key
        )
        
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for embedding requests.
        text-embedding-3-small typically uses ~1 token per 4 characters
        """
        return max(1, len(text) // 4)
    
    async def compute_embedding(self, text: str) -> List[float]:
        try:
            estimated_tokens = self.estimate_tokens(text)
            await openai_rate_limiter.acquire(estimated_tokens)
            embedding = await self.embeddings.aembed_query(text)
            return embedding
        except Exception as e:
            logger.error(f"Error computing embedding: {e}")
            raise
        
    async def _compute_embeddings_individually(self, texts: List[str]) -> List[List[float]]:

        embeddings = []        
        for i, text in enumerate(texts):
            try:
                logger.info(f"Computing embedding {i+1}/{len(texts)}: {text[:30]}...")
                embedding = await self.compute_embedding(text)
                embeddings.append(embedding)
           
                if i < len(texts) - 1:
                    status = openai_rate_limiter.get_status()
                    rpm_usage = status['rpm']['current'] / status['rpm']['limit']
                    
                    if rpm_usage > 0.8: 
                        delay = 2.0  
                    elif rpm_usage > 0.6: 
                        delay = 1.5
                    else:  
                        delay = 1.0
                    
                    logger.debug(f"Rate limit usage: {rpm_usage:.2f}, using {delay}s delay")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Failed to compute embedding for text {i+1}: {e}")
                raise
        
        return embeddings
    
    async def compute_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            total_estimated_tokens = sum(self.estimate_tokens(text) for text in texts)
            
            status = openai_rate_limiter.get_status()
            
            if (status['rpm']['remaining'] > 0 and 
                status['tpm']['remaining'] > total_estimated_tokens and
                len(texts) <= 10): 
                
                try:
                    return await self._compute_embeddings_batch_request(texts, total_estimated_tokens)
                except (openai.RateLimitError, Exception) as e:
                    logger.warning(f"Batch request failed: {e}. Falling back to individual requests.")
            
           
            logger.info(f"Using individual requests for {len(texts)} texts to respect rate limits")
            return await self._compute_embeddings_individually(texts)
        except Exception as e:
            logger.error(f"Error computing batch embeddings: {e}")
            raise
        
    def get_rate_limit_status(self) -> dict:
      
        status = openai_rate_limiter.get_status()
        recommendations = []
        
        rpm_usage = status['rpm']['current'] / status['rpm']['limit']
        tpm_usage = status['tpm']['current'] / status['tpm']['limit']
        
        if rpm_usage > 0.8:
            recommendations.append("High RPM usage - consider spacing out requests")
        if tpm_usage > 0.8:
            recommendations.append("High token usage - consider shorter texts")
        if status['rpm']['remaining'] == 0:
            recommendations.append("RPM limit reached - wait 1 minute")
        if status['tpm']['remaining'] < 1000:
            recommendations.append("Low token availability - wait or use shorter texts")
        
        status['recommendations'] = recommendations
        status['overall_health'] = 'good' if rpm_usage < 0.7 and tpm_usage < 0.7 else 'caution' if rpm_usage < 0.9 and tpm_usage < 0.9 else 'critical'
        
        return status
    
    async def test_connection(self) -> dict:
      
        try:
          
            test_text = "test"
            estimated_tokens = self.estimate_tokens(test_text)
    
            status = openai_rate_limiter.get_status()
            if status['rpm']['remaining'] == 0:
                return {
                    "status": "rate_limited",
                    "message": "Cannot test - RPM limit reached",
                    "rate_limit_status": status
                }
            
            await openai_rate_limiter.acquire(estimated_tokens)
            embedding = await self.embeddings.aembed_query(test_text)
            
            return {
                "status": "success",
                "message": "OpenAI connection working",
                "embedding_dimension": len(embedding),
                "test_tokens_used": estimated_tokens,
                "rate_limit_status": openai_rate_limiter.get_status()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "rate_limit_status": openai_rate_limiter.get_status()
            }
   
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
   
        embeddings = asyncio.run(embedding_service.compute_embeddings_batch(questions))
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