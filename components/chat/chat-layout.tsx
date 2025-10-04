"use client"

import { useState } from "react"
import { ChatSidebar } from "./chat-sidebar"
import { ChatMessages } from "./chat-messages"
import { ChatInput } from "./chat-input"
import type { Conversation, Message } from "@/lib/db"

type User = {
  id: string
  email: string
  name: string
}

type ChatLayoutProps = {
  user: User
  initialConversations: Conversation[]
  currentConversation?: Conversation
  initialMessages?: Message[]
}

export function ChatLayout({ user, initialConversations, currentConversation, initialMessages = [] }: ChatLayoutProps) {
  const [conversations, setConversations] = useState(initialConversations)
  const [messages, setMessages] = useState(initialMessages)

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <ChatSidebar
        user={user}
        conversations={conversations}
        currentConversationId={currentConversation?.id}
        onConversationsChange={setConversations}
      />

      <div className="flex flex-1 flex-col">
        <ChatMessages messages={messages} conversationTitle={currentConversation?.title} />
        <ChatInput
          conversationId={currentConversation?.id}
          onMessagesChange={setMessages}
          onConversationsChange={setConversations}
        />
      </div>
    </div>
  )
}
