"use server"

import { sql, type Conversation, type Message } from "./db"
import { getCurrentUser } from "./auth"
import { redirect } from "next/navigation"

export async function getConversations() {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  const conversations = await sql<Conversation[]>`
    SELECT * FROM conversations
    WHERE user_id = ${user.id}
    ORDER BY updated_at DESC
  `

  return conversations
}

export async function getConversation(id: string) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  const conversations = await sql<Conversation[]>`
    SELECT * FROM conversations
    WHERE id = ${id} AND user_id = ${user.id}
  `

  return conversations[0] || null
}

export async function getMessages(conversationId: string) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  const messages = await sql<Message[]>`
    SELECT m.* FROM messages m
    JOIN conversations c ON m.conversation_id = c.id
    WHERE m.conversation_id = ${conversationId}
    AND c.user_id = ${user.id}
    ORDER BY m.created_at ASC
  `

  return messages
}

export async function createConversation(title: string) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  console.log("[v0] Creating conversation for user:", user.id, "type:", typeof user.id)

  try {
    const result = await sql<Conversation[]>`
      INSERT INTO conversations (user_id, title)
      VALUES (${user.id}, ${title})
      RETURNING *
    `

    return result[0]
  } catch (error) {
    console.error("[v0] Failed to create conversation:", error)
    throw new Error(
      "Failed to create conversation. Please ensure the database migration script 005_fix_conversations_foreign_key.sql has been run.",
    )
  }
}

export async function createMessage(conversationId: string, role: "user" | "assistant", content: string) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  // Verify conversation belongs to user
  const conversation = await getConversation(conversationId)
  if (!conversation) throw new Error("Conversation not found")

  const result = await sql<Message[]>`
    INSERT INTO messages (conversation_id, role, content)
    VALUES (${conversationId}, ${role}, ${content})
    RETURNING *
  `

  // Update conversation timestamp
  await sql`
    UPDATE conversations
    SET updated_at = NOW()
    WHERE id = ${conversationId}
  `

  return result[0]
}

export async function deleteConversation(id: string) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  await sql`
    DELETE FROM conversations
    WHERE id = ${id} AND user_id = ${user.id}
  `
}
