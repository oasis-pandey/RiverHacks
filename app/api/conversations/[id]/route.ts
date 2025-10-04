import { type NextRequest, NextResponse } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { sql, type Conversation } from "@/lib/db"

// GET /api/conversations/[id] - Get single conversation
export async function GET(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params

    const conversations = await sql<Conversation[]>`
      SELECT * FROM conversations
      WHERE id = ${id} AND user_id = ${user.id}
    `

    if (conversations.length === 0) {
      return NextResponse.json({ error: "Conversation not found" }, { status: 404 })
    }

    return NextResponse.json({ conversation: conversations[0] })
  } catch (error) {
    console.error("[v0] GET /api/conversations/[id] error:", error)
    return NextResponse.json({ error: "Failed to fetch conversation" }, { status: 500 })
  }
}

// DELETE /api/conversations/[id] - Delete conversation
export async function DELETE(request: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const { id } = await params

    const result = await sql`
      DELETE FROM conversations
      WHERE id = ${id} AND user_id = ${user.id}
      RETURNING id
    `

    if (result.length === 0) {
      return NextResponse.json({ error: "Conversation not found" }, { status: 404 })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error("[v0] DELETE /api/conversations/[id] error:", error)
    return NextResponse.json({ error: "Failed to delete conversation" }, { status: 500 })
  }
}
