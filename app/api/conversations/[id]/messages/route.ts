import { type NextRequest, NextResponse } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { sql, type Message } from "@/lib/db"
import { createMessageSchema } from "@/lib/validation"
import { generateEmbedding, storeMessageEmbedding } from "@/lib/embeddings"

// GET /api/conversations/[id]/messages - List messages in conversation
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params

    // Verify conversation belongs to user
    const conversations = await sql`
      SELECT id FROM conversations
      WHERE id = ${id} AND user_id = ${user.id}
    `

    if (conversations.length === 0) {
      return NextResponse.json({ error: "Conversation not found" }, { status: 404 })
    }

    const messages = await sql<Message[]>`
      SELECT * FROM messages
      WHERE conversation_id = ${id}
      ORDER BY created_at ASC
    `

    return NextResponse.json({ messages })
  } catch (error) {
    console.error("[v0] GET /api/conversations/[id]/messages error:", error)
    return NextResponse.json({ error: "Failed to fetch messages" }, { status: 500 })
  }
}

// POST /api/conversations/[id]/messages - Create message and generate embedding
export async function POST(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params
    const body = await request.json()

    const validation = createMessageSchema.safeParse({
      ...body,
      conversationId: id,
    })

    if (!validation.success) {
      return NextResponse.json({ error: "Invalid request", details: validation.error.errors }, { status: 400 })
    }

    const { role, content } = validation.data

    // Verify conversation belongs to user
    const conversations = await sql`
      SELECT id FROM conversations
      WHERE id = ${id} AND user_id = ${user.id}
    `

    if (conversations.length === 0) {
      return NextResponse.json({ error: "Conversation not found" }, { status: 404 })
    }

    // Create message
    const result = await sql<Message[]>`
      INSERT INTO messages (conversation_id, role, content)
      VALUES (${id}, ${role}, ${content})
      RETURNING *
    `

    const message = result[0]

    // Update conversation timestamp
    await sql`
      UPDATE conversations
      SET updated_at = NOW()
      WHERE id = ${id}
    `

    // Generate and store embedding asynchronously (don't block response)
    generateEmbedding(content)
      .then((embedding) => storeMessageEmbedding(message.id, embedding))
      .catch((error) => console.error("[v0] Embedding generation failed:", error))

    return NextResponse.json({ message }, { status: 201 })
  } catch (error) {
    console.error("[v0] POST /api/conversations/[id]/messages error:", error)
    return NextResponse.json({ error: "Failed to create message" }, { status: 500 })
  }
}
