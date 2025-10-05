-- 010_create_resources_table.sql
-- Creates a table for external resources along with pgvector embeddings for retrieval.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.resources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  url TEXT UNIQUE,
  publication_date TEXT,
  authors TEXT[],
  abstract TEXT,
  content TEXT,
  metadata JSONB,
  embedding VECTOR(768) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Efficient nearest-neighbour lookup for semantic search
CREATE INDEX IF NOT EXISTS idx_resources_embedding
  ON public.resources USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
