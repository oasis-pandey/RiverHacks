-- 009_create_message_embeddings_table.sql
-- Creates the pgvector-backed message_embeddings table to store Gemini vectors.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS public.message_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES public.messages(id) ON DELETE CASCADE,
  embedding VECTOR(768) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_message_embeddings_message_id
  ON public.message_embeddings(message_id);

-- Use ivfflat for efficient nearest-neighbour search (requires ANALYZE after large imports)
CREATE INDEX IF NOT EXISTS idx_message_embeddings_vector
  ON public.message_embeddings USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
