from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.db import get_db, FAQEntry, QueryLog
from app.models.schemas import (
    QuestionRequest, QuestionResponse, FAQEntryCreate, 
    FAQEntryResponse, EmbeddingStats
)

from app.services.similarity_service import SimilarityService
from app.services.openai_service import OpenAIService
from app.services.embeddings_service import compute_embeddings_for_collection, update_embeddings_incremental, EmbeddingService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/ask-question", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    try:
        similarity_service = SimilarityService()
        openai_service = OpenAIService()
        
        similar_entry = await similarity_service.find_most_similar(
            request.user_question, db
        )
 
        if similar_entry:
            faq_entry, similarity_score = similar_entry
            response = QuestionResponse(
                source="local",
                matched_question=faq_entry.question,
                answer=faq_entry.answer,
                similarity_score=similarity_score
            )
            
            
            log_entry = QueryLog(
                user_question=request.user_question,
                matched_question=faq_entry.question,
                answer=faq_entry.answer,
                source="local",
                similarity_score=similarity_score
            )
            db.add(log_entry)
            db.commit()
            
            return response
        
        openai_answer = await openai_service.get_answer(request.user_question)
        
        response = QuestionResponse(
            source="openai",
            matched_question=None,
            answer=openai_answer
        )
        
        log_entry = QueryLog(
            user_question=request.user_question,
            answer=openai_answer,
            source="openai"
        )
        db.add(log_entry)
        db.commit()
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
@router.post("/embeddings")
async def compute_embeddings(
    collection: str = "default",
):
    try:
        task = compute_embeddings_for_collection.delay(collection)
        return {"message": f"Embedding computation started for collection: {collection}", "task_id": task.id}
    except Exception as e:
        logger.error(f"Error starting embedding computation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error starting embedding computation"
        )

@router.post("/faq-entries", response_model=FAQEntryResponse)
async def create_faq_entry(
    entry: FAQEntryCreate,
    db: Session = Depends(get_db),
):
    try:
        db_entry = FAQEntry(**entry.dict())
        db.add(db_entry)
        db.commit()
        db.refresh(db_entry)

        update_embeddings_incremental.delay([db_entry.id])
        
        return db_entry
        
    except Exception as e:
        logger.error(f"Error creating FAQ entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating FAQ entry"
        )

@router.get("/faq-entries", response_model=List[FAQEntryResponse])
async def get_faq_entries(
    collection: Optional[str] = "default",
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(FAQEntry)
    if collection:
        query = query.filter(FAQEntry.collection == collection)
    return query.offset(skip).limit(limit).all()


@router.get("/embeddings/stats", response_model=EmbeddingStats)
async def get_embedding_stats(
    db: Session = Depends(get_db),
):
    try:
        total_entries = db.query(FAQEntry).count()
        collections = db.query(FAQEntry.collection).distinct().all()
        collections = [c[0] for c in collections]
        
        return EmbeddingStats(
            total_entries=total_entries,
            collections=collections
        )
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting embedding stats"
        )

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/rate-limits")
async def get_rate_limits():
   
    try:
        embedding_service = EmbeddingService()
        status = embedding_service.get_rate_limit_status()
        
        return {
            "status": "success",
            "rate_limits": status,
            "recommendations": status.get('recommendations', []),
            "overall_health": status.get('overall_health', 'unknown')
        }
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@router.post("/test-openai")
async def test_openai_connection():
    try:
        embedding_service = EmbeddingService()
        result = await embedding_service.test_connection()
        return result
        
    except Exception as e:
        logger.error(f"Error testing OpenAI connection: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
