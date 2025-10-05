"use client"

import { useEffect, useRef } from "react"
import { Sparkles, User } from "lucide-react"
import type { Message } from "@/lib/db"
import { cn } from "@/lib/utils"
import { Skeleton } from "@/components/ui/skeleton"

type ChatMessagesProps = {
  messages: Message[]
  conversationTitle?: string
  assistantTyping?: boolean
}

export function ChatMessages({ messages, conversationTitle, assistantTyping = false }: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
    }
  }, [messages])

  if (messages.length === 0 && !assistantTyping) {
    return (
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <h2 className="mb-2 text-2xl font-bold text-foreground">{conversationTitle || "Start a New Conversation"}</h2>
          <p className="text-muted-foreground">Ask me anything about space biology, astrobiology, or life in space!</p>
        </div>
      </div>
    )
  }

  return (
    <div ref={scrollRef} className="custom-scroll flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.map((message) => (
          <div key={message.id} className={cn("flex gap-4", message.role === "user" ? "justify-end" : "justify-start")}>
            {message.role === "assistant" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
            )}

            <div
              className={cn(
                "max-w-[80%] rounded-lg px-4 py-3",
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground border border-border",
              )}
            >
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
            </div>

            {message.role === "user" && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary/10">
                <User className="h-4 w-4 text-secondary" />
              </div>
            )}
          </div>
        ))}

        {assistantTyping && (
          <div className="flex gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div className="flex max-w-[80%] items-center gap-3 rounded-lg border border-border bg-muted px-4 py-3">
              <div className="typing-indicator">
                {[0, 1, 2].map((dot) => (
                  <Skeleton
                    key={dot}
                    className="typing-dot !animate-[typing-bounce_1.2s_ease-in-out_infinite]"
                    style={{ animationDelay: `${dot * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
