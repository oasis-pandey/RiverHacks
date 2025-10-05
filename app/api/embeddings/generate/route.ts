import { type NextRequest, NextResponse } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { sql } from "@/lib/db"
import { generateEmbedding, storeMessageEmbedding } from "@/lib/embeddings"
import { generateEmbeddingSchema } from "@/lib/validation"

// POST /api/embeddings/generate - Generate embedding for a specific message
export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const body = await request.json()
    const validation = generateEmbeddingSchema.safeParse(body)

    if (!validation.success) {
      return NextResponse.json({ error: "Invalid request", details: validation.error.errors }, { status: 400 })
    }

    const { messageId } = validation.data

    // Verify message belongs to user's conversation
    const messages = await sql`
      SELECT m.id, m.content
      FROM messages m
      JOIN conversations c ON m.conversation_id = c.id
      WHERE m.id = ${messageId} AND c.user_id = ${user.id}
    `

    if (messages.length === 0) {
      return NextResponse.json({ error: "Message not found" }, { status: 404 })
    }

    const message = messages[0]

    // Generate and store embedding
    const embedding = await generateEmbedding(message.content)
    await storeMessageEmbedding(messageId, embedding)

    return NextResponse.json({
      success: true,
      messageId,
      embeddingDimensions: embedding.length,
    })
  } catch (error) {
    console.error("[v0] POST /api/embeddings/generate error:", error)
    return NextResponse.json({ error: "Failed to generate embedding" }, { status: 500 })
  }
}
