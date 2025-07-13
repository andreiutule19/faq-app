import numpy as np
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.db import FAQEntry
from app.services.embeddings_service import EmbeddingService
from app.core.settings import settings
import logging
from pgvector.sqlalchemy import Vector


logger = logging.getLogger(__name__)

class SimilarityService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.threshold = settings.similarity_threshold
    
    
    async def find_most_similar(
        self, 
        user_question: str, 
        db: Session, 
        collection: str = "default",
        limit: int = 1
    ) -> Optional[Tuple[FAQEntry, float]]:

        try:

            user_embedding = await self.embedding_service.compute_embedding(user_question)
            user_embedding = '[' + ','.join(map(str, user_embedding)) + ']'
            query = text("""
                    SELECT id, question, answer, collection, created_at, updated_at,
                           1 - (embedding <=> :user_embedding) AS similarity_score
                    FROM faq_entries
                    WHERE collection = :collection
                      AND embedding IS NOT NULL
                    ORDER BY embedding <=> :user_embedding
                    LIMIT :limit
                """)
                
            
            result = db.execute(query, {
                "user_embedding": user_embedding,
                "collection": collection,
                "limit": limit
            })
            
            rows = result.fetchall()
            
            if not rows:
                logger.warning(f"No FAQ entries found for collection: {collection}")
                return None
            
  
            best_match = rows[0]
            similarity_score = best_match.similarity_score
            
            logger.info(f"Best match found: {best_match.question} with score {similarity_score}")   
            if similarity_score >= self.threshold:
                faq_entry = FAQEntry(
                    id=best_match.id,
                    question=best_match.question,
                    answer=best_match.answer,
                    collection=best_match.collection,
                    created_at=best_match.created_at,
                    updated_at=best_match.updated_at
                )
                return faq_entry, similarity_score
            else:
                logger.info(f"Best similarity score {similarity_score} below threshold {self.threshold}")
                return None
                
        except Exception as e:
            logger.error(f"Error finding similar question: {e}")
            raise
    
