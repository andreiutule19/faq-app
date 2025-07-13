import asyncio
import sys
import os
import logging

sys.path.append('/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.db import Base, FAQEntry
from app.services.embeddings_service import EmbeddingService
from app.core.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


FAQ_DATA = [
    {
        "question": "How do I change my profile information?",
        "answer": "Navigate to your profile page, click on 'Edit Profile', and make the desired changes.",
        "collection": "default"
    },
    {
        "question": "What steps do I take to reset my password?",
        "answer": "Go to account settings, select 'Change Password', enter your current password and then the new one. Confirm the new password and save the changes.",
        "collection": "default"
    },
    {
        "question": "How can I restore my account to its default settings?",
        "answer": "In the account settings, there should be an option labeled 'Restore Default'. Clicking this will revert all custom settings back to their original state.",
        "collection": "default"
    },
    {
        "question": "Is it possible to change my registered email address?",
        "answer": "Yes, navigate to account settings, find the 'Change Email' option, enter your new email, and follow the verification process.",
        "collection": "default"
    },
    {
        "question": "How can I retrieve lost data from my account?",
        "answer": "Contact our support team with details of the lost data. They'll guide you through the recovery process.",
        "collection": "default"
    },
    {
        "question": "Are there any guidelines on setting a strong password?",
        "answer": "Absolutely! Use a combination of uppercase and lowercase letters, numbers, and special characters. Avoid using easily guessable information like birthdays or names.",
        "collection": "default"
    },
    {
        "question": "Can I set up two-factor authentication for my account?",
        "answer": "Yes, in the security section of account settings, there's an option for two-factor authentication. Follow the setup instructions provided there.",
        "collection": "default"
    },
    {
        "question": "How do I deactivate my account?",
        "answer": "Under account settings, there's a 'Deactivate Account' option. Remember, this action is irreversible.",
        "collection": "default"
    },
    {
        "question": "What do I do if my account has been compromised?",
        "answer": "Immediately reset your password and contact our security team for further guidance.",
        "collection": "default"
    },
    {
        "question": "Can I customize the notifications I receive?",
        "answer": "Yes, head to the notifications settings in your account and choose which ones you'd like to receive.",
        "collection": "default"
    }
]

def create_database_extensions():
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            logger.info("Created pgvector extension")
    except Exception as e:
        logger.error(f"Error creating extensions: {e}")
        raise

def create_database_tables():
    try:
        engine = create_engine(settings.database_url)
        Base.metadata.create_all(bind=engine)
        logger.info("Created database tables")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

def create_database_indexes():
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_faq_entries_collection ON faq_entries(collection);",
                "CREATE INDEX IF NOT EXISTS idx_faq_entries_embedding ON faq_entries USING ivfflat (embedding vector_cosine_ops);",
                "CREATE INDEX IF NOT EXISTS idx_query_logs_created_at ON query_logs(created_at);",
                "CREATE INDEX IF NOT EXISTS idx_query_logs_source ON query_logs(source);"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
            
            conn.commit()
            logger.info("Created database indexes")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise

def insert_faq_data():

    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
     
        existing_count = db.query(FAQEntry).count()
        if existing_count > 0:
            logger.info(f"📋 FAQ data already exists ({existing_count} entries). Skipping insertion.")
            db.close()
            return
        
        faq_entries = []
        for faq_item in FAQ_DATA:
            faq_entry = FAQEntry(
                question=faq_item["question"],
                answer=faq_item["answer"],
                collection=faq_item["collection"]
            )
            faq_entries.append(faq_entry)
        
        db.add_all(faq_entries)
        db.commit()
        
        logger.info(f"Inserted {len(faq_entries)} FAQ entries")
        db.close()
        
    except Exception as e:
        logger.error(f"Error inserting FAQ data: {e}")
        raise

async def generate_and_store_embeddings():

    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        entries_without_embeddings = db.query(FAQEntry).filter(
            FAQEntry.embedding.is_(None)
        ).all()
        
        if not entries_without_embeddings:
            logger.info("📋 All FAQ entries already have embeddings!")
            db.close()
            return
        
        logger.info(f"🔄 Generating embeddings for {len(entries_without_embeddings)} entries...")
        
        embedding_service = EmbeddingService()
        questions = [entry.question for entry in entries_without_embeddings]
        
        logger.info("🧠 Computing embeddings using OpenAI API...")
        embeddings = await embedding_service.compute_embeddings_batch(questions)
        
        for entry, embedding in zip(entries_without_embeddings, embeddings):
            entry.embedding = embedding
            logger.info(f"✅ Generated embedding for: {entry.question[:60]}...")
        

        db.commit()
        db.close()
        
        logger.info(f"Successfully generated and stored embeddings for {len(entries_without_embeddings)} FAQ entries!")
        
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        if 'db' in locals():
            db.rollback()
            db.close()
        raise

async def verify_setup():

    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        total_entries = db.query(FAQEntry).count()
        entries_with_embeddings = db.query(FAQEntry).filter(
            FAQEntry.embedding.is_not(None)
        ).count()
        
        logger.info(f"Database verification:")
        logger.info(f"Total FAQ entries: {total_entries}")
        logger.info(f"Entries with embeddings: {entries_with_embeddings}")
        logger.info(f"Setup completion: {entries_with_embeddings}/{total_entries}")
        
        if entries_with_embeddings == total_entries and total_entries > 0:
            logger.info("Database initialization completed successfully!")
        else:
            logger.warning("Some entries are missing embeddings")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Error during verification: {e}")
        raise

async def main():
    logger.info("Starting database initialization with embeddings...")
    
    try:

        logger.info("1 Creating PostgreSQL extensions...")
        create_database_extensions()
        
        logger.info("2 Creating database tables...")
        create_database_tables()
        
        logger.info("3 Creating database indexes...")
        create_database_indexes()
        
        logger.info("4 Inserting FAQ data...")
        insert_faq_data()

        logger.info("5 Generating embeddings...")
        await generate_and_store_embeddings()
        
        logger.info("6 Verifying setup...")
        await verify_setup()
        
        logger.info("✨ Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())