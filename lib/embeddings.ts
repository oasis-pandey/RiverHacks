"use server"

import { GoogleGenerativeAI } from "@google/generative-ai"
import { sql } from "./db"

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "")

/**
 * Generate embedding for text using Gemini's text-embedding-004 model
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  try {
    const model = genAI.getGenerativeModel({ model: "text-embedding-004" })
    const result = await model.embedContent(text)
    return result.embedding.values
  } catch (error) {
    console.error("[v0] Embedding generation error:", error)
    throw new Error("Failed to generate embedding")
  }
}

/**
 * Store embedding for a message
 */
export async function storeMessageEmbedding(messageId: string, embedding: number[]) {
  const embeddingStr = `[${embedding.join(",")}]`

  await sql`
    INSERT INTO message_embeddings (message_id, embedding)
    VALUES (${messageId}, ${embeddingStr}::vector)
    ON CONFLICT (message_id) 
    DO UPDATE SET embedding = ${embeddingStr}::vector, created_at = NOW()
  `
}

type SemanticSearchOptions = {
  limit?: number
  page?: number
  similarityThreshold?: number
  conversationId?: string
  role?: "user" | "assistant" | "system"
  sort?: "similarity" | "recent"
}

/**
 * Perform semantic search across user's messages
 */
export async function semanticSearch(userId: string, queryEmbedding: number[], options: SemanticSearchOptions = {}) {
  const {
    limit = 10,
    page = 1,
    similarityThreshold = 0.7,
    conversationId,
    role,
    sort = "similarity",
  } = options

  const offset = Math.max(page - 1, 0) * limit
  const embeddingStr = `[${queryEmbedding.join(",")}]`

  const conversationFilter = conversationId ? sql`AND m.conversation_id = ${conversationId}` : sql``
  const roleFilter = role ? sql`AND m.role = ${role}` : sql``
  const orderByClause =
    sort === "recent" ? sql`ORDER BY m.created_at DESC` : sql`ORDER BY me.embedding <=> ${embeddingStr}::vector`

  const results = await sql`
    SELECT 
      m.id,
      m.conversation_id,
      m.role,
      m.content,
      m.created_at,
      c.title as conversation_title,
      1 - (me.embedding <=> ${embeddingStr}::vector) as similarity
    FROM message_embeddings me
    JOIN messages m ON me.message_id = m.id
    JOIN conversations c ON m.conversation_id = c.id
    WHERE c.user_id = ${userId}
      ${conversationFilter}
      ${roleFilter}
      AND 1 - (me.embedding <=> ${embeddingStr}::vector) >= ${similarityThreshold}
    ${orderByClause}
    LIMIT ${limit} OFFSET ${offset}
  `

  const totalResult = await sql`
    SELECT COUNT(*)::int AS total
    FROM message_embeddings me
    JOIN messages m ON me.message_id = m.id
    JOIN conversations c ON m.conversation_id = c.id
    WHERE c.user_id = ${userId}
      ${conversationFilter}
      ${roleFilter}
      AND 1 - (me.embedding <=> ${embeddingStr}::vector) >= ${similarityThreshold}
  `

  const total = totalResult[0]?.total ? Number(totalResult[0].total) : 0

  return {
    results,
    total,
  }
}
