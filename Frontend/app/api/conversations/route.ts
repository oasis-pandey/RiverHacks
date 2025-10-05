import { type NextRequest, NextResponse } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { sql, type Conversation } from "@/lib/db"
import { createConversationSchema } from "@/lib/validation"

// GET /api/conversations - List all conversations for current user
export async function GET() {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const conversations = await sql<Conversation[]>`
      SELECT * FROM conversations
      WHERE user_id = ${user.id}
      ORDER BY updated_at DESC
    `

    return NextResponse.json({ conversations })
  } catch (error) {
    console.error("[v0] GET /api/conversations error:", error)
    return NextResponse.json({ error: "Failed to fetch conversations" }, { status: 500 })
  }
}

// POST /api/conversations - Create new conversation
export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const body = await request.json()
    const validation = createConversationSchema.safeParse(body)

    if (!validation.success) {
      return NextResponse.json({ error: "Invalid request", details: validation.error.errors }, { status: 400 })
    }

    const { title } = validation.data

    const result = await sql<Conversation[]>`
      INSERT INTO conversations (user_id, title)
      VALUES (${user.id}, ${title})
      RETURNING *
    `

    return NextResponse.json({ conversation: result[0] }, { status: 201 })
  } catch (error) {
    console.error("[v0] POST /api/conversations error:", error)
    return NextResponse.json({ error: "Failed to create conversation" }, { status: 500 })
  }
}
