import { z } from "zod"

export const createConversationSchema = z.object({
  title: z.string().min(1).max(200),
})

export const createMessageSchema = z.object({
  conversationId: z.string().uuid(),
  role: z.enum(["user", "assistant", "system"]),
  content: z.string().min(1).max(10000),
})

export const semanticSearchSchema = z.object({
  query: z.string().min(1).max(1000),
  limit: z.number().int().min(1).max(20).optional().default(5),
  similarityThreshold: z.number().min(0).max(1).optional().default(0.7),
})

export const generateEmbeddingSchema = z.object({
  messageId: z.string().uuid(),
})
