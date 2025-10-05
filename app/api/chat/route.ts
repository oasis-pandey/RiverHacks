import type { NextRequest } from "next/server"
import { getCurrentUser } from "@/lib/auth"

// POST /api/chat - Chat endpoint using Gemini REST API
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

    // Build Gemini contents payload following REST quickstart format
    const systemInstruction = `You are a knowledgeable space biology expert. Help users understand astrobiology, space medicine, extremophiles, and life in space. Provide accurate, engaging, and educational responses.`

    const contents = [
      {
        role: "user",
        parts: [{ text: systemInstruction }],
      },
      ...messages
        .filter((msg: any) => typeof msg?.content === "string" && msg.content.trim().length > 0)
        .map((msg: any) => ({
          role: msg.role === "assistant" ? "model" : "user",
          parts: [{ text: msg.content }],
        })),
    ]

    // Call Gemini API
    const apiKey = process.env.GEMINI_API_KEY
    if (!apiKey) {
      console.error("[v0] GEMINI_API_KEY environment variable is missing")
      return new Response("Gemini API key not configured", { status: 500 })
    }

    const rawModel = process.env.GEMINI_API_MODEL || "gemini-2.5-pro"
    const modelPath = rawModel.startsWith("models/") ? rawModel : `models/${rawModel}`
    const apiVersion = process.env.GEMINI_API_VERSION || "v1beta"
    const url = `https://generativelanguage.googleapis.com/${apiVersion}/${modelPath}:streamGenerateContent?key=${apiKey}&alt=sse`

    const geminiResponse = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        contents,
        generationConfig: {
          temperature: 0.7,
          topK: 40,
          topP: 0.95,
          maxOutputTokens: 2048,
        },
      }),
    })

    if (!geminiResponse.ok) {
      const errorText = await geminiResponse.text()
      console.error("[v0] Gemini API error:", errorText)
      throw new Error(`Gemini API error: ${geminiResponse.status}`)
    }

    // Stream the response
    const stream = new ReadableStream({
      async start(controller) {
        try {
          const reader = geminiResponse.body?.getReader()
          const decoder = new TextDecoder()

          if (!reader) {
            throw new Error("No response body")
          }

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value, { stream: true })
            const lines = chunk.split('\n')

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                if (data === '[DONE]') continue
                
                try {
                  const parsed = JSON.parse(data)
                  const text = parsed.candidates?.[0]?.content?.parts?.[0]?.text
                  if (text) {
                    controller.enqueue(new TextEncoder().encode(text))
                  }
                } catch (e) {
                  // Skip invalid JSON
                }
              }
            }
          }
          controller.close()
        } catch (error) {
          console.error("[v0] Stream error:", error)
          controller.error(error)
        }
      }
    })

    return new Response(stream, {
      headers: {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
      },
    })
  } catch (error) {
    console.error("[v0] POST /api/chat error:", error)
    return new Response("Failed to generate response", { status: 500 })
  }
}
