CREATE EXTENSION IF NOT EXISTS vector;

DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL extensions enabled successfully!';
    RAISE NOTICE 'Run init.py to complete the database initialization with embeddings.';
END $$;