import { SearchExperience } from "@/components/search/search-experience"
import { listResources } from "@/lib/resources"

export default async function SearchPage() {
  const resources = await listResources()

  return (
    <main className="container mx-auto max-w-6xl px-6 pb-16 pt-10 md:px-8 md:pb-20 md:pt-14">
      <div className="space-y-8">
        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-foreground md:text-4xl">
            Explore space biology resources
          </h1>
          <p className="max-w-3xl text-base text-muted-foreground">
            Browse curated programs, research portals, and commercial opportunities that advance life sciences in
            space. Filter by category or keyword to surface the missions and initiatives that matter most to your next
            project.
          </p>
        </div>

        <SearchExperience resources={resources} />
      </div>
    </main>
  )
}
