import { redirect } from "next/navigation"
import { getCurrentUser } from "@/lib/auth"
import { getConversations } from "@/lib/conversations"
import { ChatLayout } from "@/components/chat/chat-layout"

export default async function ChatPage() {
  const user = await getCurrentUser()
  if (!user) redirect("/auth/signin")

  const conversations = await getConversations()

  return <ChatLayout user={user} initialConversations={conversations} />
}
