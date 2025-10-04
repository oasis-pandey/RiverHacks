import { type NextRequest, NextResponse } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { generateEmbedding, semanticSearch } from "@/lib/embeddings"
import { semanticSearchSchema } from "@/lib/validation"

// POST /api/search/semantic - Perform semantic search across user's messages
export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser()
    if (!user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }

    const body = await request.json()
    const validation = semanticSearchSchema.safeParse(body)

    if (!validation.success) {
      return NextResponse.json({ error: "Invalid request", details: validation.error.errors }, { status: 400 })
    }

    const { query, limit, similarityThreshold } = validation.data

    // Generate embedding for search query
    const queryEmbedding = await generateEmbedding(query)

    // Perform semantic search
    const results = await semanticSearch(user.id, queryEmbedding, limit, similarityThreshold)

    return NextResponse.json({
      results,
      count: results.length,
    })
  } catch (error) {
    console.error("[v0] POST /api/search/semantic error:", error)
    return NextResponse.json({ error: "Failed to perform semantic search" }, { status: 500 })
  }
}
