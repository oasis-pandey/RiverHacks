import type { NextRequest } from "next/server"
import { getCurrentUser } from "@/lib/auth"
import { generateEmbedding, semanticSearch } from "@/lib/embeddings"

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

    type RetrievedMessage = {
      id: string
      conversation_id: string
      role: "user" | "assistant" | "system"
      content: string
      created_at: string
      conversation_title: string
      similarity: number
    }

    const latestUserMessage = [...messages]
      .reverse()
      .find((msg: any) => msg?.role === "user" && typeof msg.content === "string" && msg.content.trim().length > 0)

    let retrievedContext: RetrievedMessage[] = []

    if (latestUserMessage) {
      try {
        const queryEmbedding = await generateEmbedding(latestUserMessage.content)
        const searchResult = await semanticSearch(user.id, queryEmbedding, {
          limit: 6,
          similarityThreshold: 0.72,
          sort: "similarity",
        })

        retrievedContext = (searchResult.results ?? []) as RetrievedMessage[]
      } catch (error) {
        console.error("[v0] Failed to retrieve semantic context:", error)
      }
    }

    const contextText =
      retrievedContext.length > 0
        ? [
            "Here are relevant notes from your past chats. Use them when helpful:",
            ...retrievedContext.slice(0, 6).map((item, index) => {
              const timestamp = new Date(item.created_at).toISOString()
              const similarity = item.similarity?.toFixed?.(2) ?? ""
              return `${index + 1}. [${item.role.toUpperCase()} • ${item.conversation_title} • ${timestamp} • sim ${similarity}] ${item.content}`
            }),
          ].join("\n")
        : ""

    const normalizedMessages = messages
      .filter((msg: any) => typeof msg?.content === "string" && msg.content.trim().length > 0)
      .map((msg: any) => ({
        role: msg.role === "assistant" ? "model" : "user",
        parts: [{ text: msg.content }],
      }))

    const contents = [
      {
        role: "user",
        parts: [{ text: systemInstruction }],
      },
      ...(contextText
        ? [
            {
              role: "user" as const,
              parts: [{ text: contextText }],
            },
          ]
        : []),
      ...normalizedMessages,
    ]

    // If a HYBRID_CHAT_ENDPOINT is configured, call it with the RAG-style payload
    const hybridEndpoint = process.env.HYBRID_CHAT_ENDPOINT
    const hybridApiKey = process.env.HYBRID_CHAT_API_KEY

    if (hybridEndpoint) {
      try {
        // Build a single text context combining system instruction, retrieved context, and recent messages
        const conversationContext = [
          systemInstruction,
          contextText,
          ...(normalizedMessages || []).map((m: any, idx: number) => `${m.role}: ${m.parts?.[0]?.text ?? ""}`),
        ]
          .filter(Boolean)
          .join("\n\n")

        const ragPayload: any = {
          question: latestUserMessage?.content ?? "",
          k: 6,
          probes: 12,
          web: {
            google: true,
            scholar: true,
            scrape: false,
            fetch_pdfs: false,
            max_results: 3,
          },
          thread_id: "hybrid",
          // common, easy-to-consume fields
          system: systemInstruction,
          context: conversationContext,
          messages: normalizedMessages,
          additionalProp1: {
            systemInstruction,
            contextText,
            messages: normalizedMessages,
          },
        }

        // Debug: log trimmed payload for diagnostics (no secrets)
        try {
          console.debug("[v0] Hybrid payload question:", ragPayload.question)
          console.debug("[v0] Hybrid payload system length:", String(ragPayload.system).length)
          console.debug("[v0] Hybrid payload context length:", String(ragPayload.context).length)
        } catch (e) {
          /* ignore logging errors */
        }

        // Log payload (trimmed) for debugging
        try {
          const safePayloadPreview = JSON.stringify({
            question: String(ragPayload.question).slice(0, 500),
            systemLength: String(ragPayload.system).length,
            contextLength: String(ragPayload.context).length,
          })
          console.debug("[v0] Posting to hybrid endpoint:", safePayloadPreview)
        } catch (e) {
          /* ignore */
        }

        const hybridResp = await fetch(hybridEndpoint, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(hybridApiKey ? { Authorization: `Bearer ${hybridApiKey}` } : {}),
          },
          body: JSON.stringify(ragPayload),
        })

        if (!hybridResp.ok) {
          const errText = await hybridResp.text().catch(() => "")
          console.error("[v0] Hybrid endpoint error:", hybridResp.status, errText)
          throw new Error(`Hybrid endpoint error: ${hybridResp.status}`)
        }

        // Read a preview of the response for debugging (without consuming the full stream if possible)
  const contentType = hybridResp.headers.get("content-type") || ""
  if (hybridResp.body && contentType.includes("text")) {
          // For text streams, read a small chunk and then recreate a stream for forwarding
          const reader = hybridResp.body.getReader()
          const decoder = new TextDecoder()
          let preview = ""
          let done = false
          let chunks: Uint8Array[] = []

          try {
            while (!done && preview.length < 2000) {
              const res = await reader.read()
              done = !!res.done
              if (res.value) {
                chunks.push(res.value)
                preview += decoder.decode(res.value, { stream: true })
              }
            }
          } catch (e) {
            console.warn("[v0] Error reading hybrid preview:", e)
          }

          // Log the preview (trimmed)
          try {
            console.debug("[v0] Hybrid response preview:", preview.slice(0, 2000))
          } catch (e) {
            /* ignore */
          }

          // Reconstruct a new stream that yields the chunks we've consumed + the rest from the original reader
          const stream = new ReadableStream({
            async start(controller) {
              try {
                for (const c of chunks) controller.enqueue(c)
                if (!done) {
                  // pump remaining data from the original reader
                  while (true) {
                    const r = await reader.read()
                    if (r.done) break
                    controller.enqueue(r.value)
                  }
                }
                controller.close()
              } catch (e) {
                controller.error(e)
              }
            },
          })

          return new Response(stream, {
            headers: {
              "Content-Type": contentType || "text/plain; charset=utf-8",
              "Cache-Control": "no-cache",
              "Connection": "keep-alive",
            },
          })
        }

        // Otherwise, parse JSON/text and return as plain text
        const respContentType = hybridResp.headers.get("content-type") || ""
        if (respContentType.includes("application/json")) {
          const json = await hybridResp.json()
          // Try to extract a reasonable text field
          const text = (json?.answer || json?.text || JSON.stringify(json)) as string
          return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } })
        }

        const text = await hybridResp.text()
        return new Response(text, { headers: { "Content-Type": "text/plain; charset=utf-8" } })
      } catch (error) {
        console.error("[v0] Failed to call HYBRID_CHAT_ENDPOINT:", error)
        return new Response("Hybrid endpoint error", { status: 502 })
      }
    }

    // Fallback: call Gemini API
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
        const reader = geminiResponse.body?.getReader()
        const decoder = new TextDecoder()
        const encoder = new TextEncoder()
        let buffer = ""

        if (!reader) {
          controller.error(new Error("No response body"))
          return
        }

        const processBuffer = () => {
          let newlineIndex = buffer.indexOf("\n")

          while (newlineIndex !== -1) {
            const rawLine = buffer.slice(0, newlineIndex)
            buffer = buffer.slice(newlineIndex + 1)
            const line = rawLine.replace(/\r$/, "").trim()

            if (!line || line.startsWith(":")) {
              newlineIndex = buffer.indexOf("\n")
              continue
            }

            if (line.startsWith("data: ")) {
              const data = line.slice(6).trim()
              if (!data || data === "[DONE]") {
                newlineIndex = buffer.indexOf("\n")
                continue
              }

              try {
                const parsed = JSON.parse(data)
                const text = parsed.candidates?.[0]?.content?.parts?.[0]?.text
                if (text) {
                  controller.enqueue(encoder.encode(text))
                }
              } catch (parseError) {
                console.warn("[v0] Unable to parse Gemini stream chunk", parseError)
              }
            }

            newlineIndex = buffer.indexOf("\n")
          }
        }

        try {
          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            buffer += decoder.decode(value, { stream: true })
            processBuffer()
          }

          buffer += decoder.decode()
          processBuffer()
          controller.close()
        } catch (error) {
          console.error("[v0] Stream error:", error)
          controller.error(error)
        }
      },
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
