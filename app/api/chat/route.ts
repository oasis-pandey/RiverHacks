import type { NextRequest } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { streamText } from "ai"

// POST /api/chat - Chat endpoint (RAG disabled for now, will add later)
export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return new Response("Unauthorized", { status: 401 })
    }

    const { messages } = await request.json()

    if (!messages || !Array.isArray(messages) || messages.length === 0) {
      return new Response("Invalid messages", { status: 400 })
    }

    const result = streamText({
      model: "google/gemini-1.5-flash",
      system: `You are a knowledgeable space biology expert. Help users understand astrobiology, space medicine, extremophiles, and life in space. Provide accurate, engaging, and educational responses.`,
      messages,
    })

    return result.toDataStreamResponse()
  } catch (error) {
    console.error("[v0] POST /api/chat error:", error)
    return new Response("Failed to generate response", { status: 500 })
  }
}
