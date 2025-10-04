"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Sparkles, Plus, MessageSquare, Trash2, LogOut } from "lucide-react"
import { createConversation, deleteConversation } from "@/lib/conversations"
import { signOut } from "@/lib/auth"
import type { Conversation } from "@/lib/db"
import { cn } from "@/lib/utils"

type User = {
  id: string
  email: string
  name: string
}

type ChatSidebarProps = {
  user: User
  conversations: Conversation[]
  currentConversationId?: string
  onConversationsChange: (conversations: Conversation[]) => void
}

export function ChatSidebar({ user, conversations, currentConversationId, onConversationsChange }: ChatSidebarProps) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  async function handleNewChat() {
    setLoading(true)
    const conversation = await createConversation("New Conversation")
    onConversationsChange([conversation, ...conversations])
    router.push(`/chat/${conversation.id}`)
    setLoading(false)
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation()
    await deleteConversation(id)
    onConversationsChange(conversations.filter((c) => c.id !== id))
    if (currentConversationId === id) {
      router.push("/chat")
    }
  }

  return (
    <div className="flex h-full w-80 flex-col border-r border-sidebar-border bg-sidebar">
      <div className="flex items-center justify-between border-b border-sidebar-border p-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-sidebar-primary" />
          <span className="font-mono text-lg font-bold text-sidebar-foreground">SpaceBio</span>
        </div>
      </div>

      <div className="p-4">
        <Button
          onClick={handleNewChat}
          disabled={loading}
          className="w-full bg-sidebar-primary text-sidebar-primary-foreground hover:bg-sidebar-primary/90"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Chat
        </Button>
      </div>

      <ScrollArea className="flex-1 px-4">
        <div className="space-y-2">
          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => router.push(`/chat/${conversation.id}`)}
              className={cn(
                "group flex w-full items-center justify-between rounded-lg p-3 text-left transition-colors",
                currentConversationId === conversation.id
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50",
              )}
            >
              <div className="flex items-center gap-2 overflow-hidden">
                <MessageSquare className="h-4 w-4 shrink-0" />
                <span className="truncate text-sm">{conversation.title}</span>
              </div>
              <button
                onClick={(e) => handleDelete(conversation.id, e)}
                className="shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground hover:text-destructive" />
              </button>
            </button>
          ))}
        </div>
      </ScrollArea>

      <div className="border-t border-sidebar-border p-4">
        <div className="mb-3 flex items-center gap-2 text-sm text-sidebar-foreground">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-sidebar-primary text-sidebar-primary-foreground">
            {user.name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="truncate font-medium">{user.name}</p>
            <p className="truncate text-xs text-muted-foreground">{user.email}</p>
          </div>
        </div>
        <form action={signOut}>
          <Button variant="outline" size="sm" className="w-full bg-transparent" type="submit">
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </Button>
        </form>
      </div>
    </div>
  )
}
