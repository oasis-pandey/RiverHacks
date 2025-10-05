import { getCurrentUser } from "@/lib/auth"
import { SiteHeaderClient } from "@/components/site-header-client"

export async function SiteHeader() {
  const user = await getCurrentUser()

  const safeUser = user
    ? {
        id: String(user.id),
        email: String(user.email),
        name: user.name ? String(user.name) : null,
      }
    : null

  return <SiteHeaderClient user={safeUser} />
}
