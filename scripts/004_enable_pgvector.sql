-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create message_embeddings table for storing vector embeddings
CREATE TABLE IF NOT EXISTS message_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
  embedding vector(768), -- Gemini text-embedding-004 produces 768-dimensional vectors
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(message_id)
);

-- Create index for fast similarity search using cosine distance
CREATE INDEX IF NOT EXISTS idx_message_embeddings_vector 
  ON message_embeddings 
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);

-- Create index for message_id lookups
CREATE INDEX IF NOT EXISTS idx_message_embeddings_message_id 
  ON message_embeddings(message_id);
