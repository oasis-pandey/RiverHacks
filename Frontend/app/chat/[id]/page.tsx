import { redirect } from "next/navigation"
import { getCurrentUser } from "@/lib/auth"
import { getConversations, getConversation, getMessages } from "@/lib/conversations"
import { ChatLayout } from "@/components/chat/chat-layout"

export default async function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  const { id } = await params
  const [conversations, conversation, messages] = await Promise.all([
    getConversations(),
    getConversation(id),
    getMessages(id),
  ])

  if (!conversation) redirect("/chat")

  return (
    <ChatLayout
      user={user}
      initialConversations={conversations}
      currentConversation={conversation}
      initialMessages={messages}
    />
  )
}
