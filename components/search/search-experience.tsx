"use client"

import * as React from "react"
import Image from "next/image"
import { useRouter } from "next/navigation"
import { Filter, Search as SearchIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { SpaceResource } from "@/lib/resources"

type SearchExperienceProps = {
  resources: SpaceResource[]
}

type FiltersState = {
  query: string
  category: string
}

export function SearchExperience({ resources }: SearchExperienceProps) {
  const router = useRouter()
  const [filters, setFilters] = React.useState<FiltersState>({ query: "", category: "all" })

  const categories = React.useMemo(() => {
    const unique = new Set<string>(resources.map((resource) => resource.category))
    return ["all", ...Array.from(unique).sort((a, b) => a.localeCompare(b))]
  }, [resources])

  const filteredResources = React.useMemo(() => {
    const normalizedQuery = filters.query.trim().toLowerCase()
    return resources.filter((resource) => {
      const matchesCategory = filters.category === "all" || resource.category === filters.category
      if (!normalizedQuery) return matchesCategory

      const haystack = [resource.title, resource.description, resource.category, resource.tags.join(" ")]
        .join(" ")
        .toLowerCase()

      return matchesCategory && haystack.includes(normalizedQuery)
    })
  }, [filters, resources])

  const handleSubmit = React.useCallback(
    (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault()
    },
    [],
  )

  return (
    <div className="space-y-6">
      <Card className="border-border/70">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-xl font-semibold">
            <SearchIcon className="h-5 w-5 text-primary" />
            Discover resources
          </CardTitle>
          <CardDescription>Explore curated websites and programs across the space biology ecosystem.</CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <form onSubmit={handleSubmit} className="grid gap-4 lg:gap-6">
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
              <div className="space-y-2">
                <Label htmlFor="resource-query" className="text-sm font-medium">
                  Search resources
                </Label>
                <Input
                  id="resource-query"
                  placeholder="Search by mission, agency, keyword, or tag..."
                  value={filters.query}
                  onChange={(event) => setFilters((prev) => ({ ...prev, query: event.target.value }))}
                />
              </div>
              <Button type="submit" variant="default" className="md:w-36">
                Search
              </Button>
            </div>

            <div className="rounded-lg border border-dashed border-border/60 bg-muted/10 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                <Filter className="h-4 w-4" />
                Filter
              </div>

              <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div className="space-y-2">
                  <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Category</Label>
                  <Select
                    value={filters.category}
                    onValueChange={(value) => setFilters((prev) => ({ ...prev, category: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All categories" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectLabel>Categories</SelectLabel>
                        {categories.map((category) => (
                          <SelectItem key={category} value={category} className="capitalize">
                            {category === "all" ? "All categories" : category}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      <section className="space-y-4">
        {filteredResources.length === 0 ? (
          <Card className="border-border/70 bg-muted/5">
            <CardContent className="flex flex-col items-center justify-center gap-3 py-12 text-center">
              <SearchIcon className="h-8 w-8 text-muted-foreground" />
              <div className="space-y-1">
                <h3 className="text-lg font-semibold text-foreground">No resources found</h3>
                <p className="text-sm text-muted-foreground">
                  Try a different search term or broaden your category filter.
                </p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {filteredResources.map((resource) => (
              <Card
                key={resource.slug}
                className="group flex h-full flex-col overflow-hidden border-border/70 bg-card/70 transition hover:border-primary/60 hover:shadow-lg"
              >
                <div className="relative h-40 w-full overflow-hidden bg-muted">
                  <Image
                    src={resource.image}
                    alt={resource.title}
                    fill
                    className="object-cover transition duration-500 group-hover:scale-105"
                    sizes="(min-width: 1280px) 33vw, (min-width: 640px) 50vw, 100vw"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent" />
                  <div className="absolute bottom-3 left-3 flex items-center gap-2">
                    <Badge variant="secondary" className="bg-secondary/80 text-secondary-foreground">
                      {resource.category}
                    </Badge>
                  </div>
                </div>

                <CardHeader className="space-y-3">
                  <div className="space-y-1.5">
                    <CardTitle className="text-lg font-semibold text-foreground">
                      {resource.title}
                    </CardTitle>
                    <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                      {resource.description}
                    </CardDescription>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {resource.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="border-border/70 text-xs uppercase tracking-wide">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardHeader>

                <CardFooter className="mt-auto flex items-center justify-between border-t border-border/50 bg-card/60 px-6 py-4">
                  <Button
                    variant="default"
                    className="w-full justify-center"
                    onClick={() => router.push(`/search/${resource.slug}`)}
                  >
                    View details
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </section>

      <div className="rounded-lg border border-border/70 bg-muted/5 p-4 text-sm text-muted-foreground">
        <p>
          This library grows alongside the space biology ecosystem. Share new programs or opportunities and we&apos;ll add
          them to the catalog so everyone can discover what&apos;s next.
        </p>
      </div>
    </div>
  )
}
