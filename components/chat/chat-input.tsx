"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Send } from "lucide-react"
import { createConversation, createMessage } from "@/lib/conversations"
import type { Conversation, Message } from "@/lib/db"

type ChatInputProps = {
  conversationId?: string
  onMessagesChange: (updater: Message[] | ((prev: Message[]) => Message[])) => void
  onConversationsChange: (conversations: Conversation[]) => void
  onAssistantTypingChange?: (isTyping: boolean) => void
}

export function ChatInput({ conversationId, onMessagesChange, onConversationsChange, onAssistantTypingChange }: ChatInputProps) {
  const router = useRouter()
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim() || loading) return

    setLoading(true)
    const userMessage = input.trim()
    setInput("")
  onAssistantTypingChange?.(true)

    try {
      let currentConversationId = conversationId

      // Create new conversation if none exists
      if (!currentConversationId) {
        const conversation = await createConversation(userMessage.slice(0, 50)) as Conversation
        currentConversationId = conversation.id
        onConversationsChange([conversation])
        router.push(`/chat/${conversation.id}`)
      }

      // Save user message (at this point currentConversationId is guaranteed to be defined)
      const userMsg = await createMessage(currentConversationId!, "user", userMessage) as Message
      onMessagesChange((prev: Message[]) => [...prev, userMsg])

      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: userMessage }],
        }),
      })

      if (!response.ok) {
        throw new Error("Failed to get AI response")
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let assistantResponse = ""

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          assistantResponse += chunk
        }
      }

      // Save assistant message
      const assistantMsg = await createMessage(currentConversationId!, "assistant", assistantResponse) as Message
      onMessagesChange((prev: Message[]) => [...prev, assistantMsg])
    } catch (error) {
      console.error("[v0] Chat error:", error)
      alert("Failed to get response. Please try again.")
    } finally {
      setLoading(false)
      onAssistantTypingChange?.(false)
    }
  }

  return (
    <div className="border-t border-border bg-background p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
        <div className="flex gap-2">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about space biology, astrobiology, or life in extreme environments..."
            className="min-h-[60px] resize-none bg-muted text-foreground"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleSubmit(e)
              }
            }}
          />
          <Button
            type="submit"
            size="icon"
            disabled={!input.trim() || loading}
            className="h-[60px] w-[60px] shrink-0 bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Send className="h-5 w-5" />
          </Button>
        </div>
        <p className="mt-2 text-xs text-muted-foreground">Press Enter to send, Shift+Enter for new line</p>
      </form>
    </div>
  )
}
