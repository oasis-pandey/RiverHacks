"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Filter, Search as SearchIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { Resource } from "@/lib/resources"

const SUMMARY_MAX_CHARS = 180
const PAGE_SIZE = 12

type SearchExperienceProps = {
  resources: Resource[]
}

type FiltersState = {
  query: string
  category: string
}

type CategoryOption = {
  value: string
  label: string
}

type EnrichedResource = Resource & {
  category: string
  normalizedCategory: string
  tags: string[]
  summary: string
}

function deriveCategory(resource: Resource): string {
  const sections = Array.isArray(resource.metadata?.sections)
    ? (resource.metadata?.sections as unknown[]).map((section) => String(section))
    : []

  if (sections.length > 0) {
    const firstSection = sections.find((section) => section.trim().length > 0)
    if (firstSection) {
      return firstSection.trim()
    }
  }

  return resource.publicationDate ? "Publication" : "Resource"
}

function deriveTags(resource: Resource): string[] {
  const tags = new Set<string>()

  if (Array.isArray(resource.metadata?.sections)) {
    for (const section of resource.metadata.sections as unknown[]) {
      const normalized = String(section)
      if (normalized) tags.add(normalized)
    }
  }

  for (const author of resource.authors) {
    if (author) tags.add(author)
  }

  const doi = resource.metadata?.doi
  if (typeof doi === "string" && doi.trim()) {
    tags.add(`DOI: ${doi}`)
  }

  return Array.from(tags)
}

function deriveSummary(resource: Resource): string {
  if (resource.abstract) {
    const condensed = resource.abstract.replace(/\s+/g, " ").trim()
    return condensed.length > SUMMARY_MAX_CHARS ? `${condensed.slice(0, SUMMARY_MAX_CHARS - 1)}…` : condensed
  }

  if (resource.content) {
    const condensed = resource.content.replace(/\s+/g, " ").trim()
    return condensed.length > SUMMARY_MAX_CHARS ? `${condensed.slice(0, SUMMARY_MAX_CHARS - 1)}…` : condensed
  }

  return "Detailed space biology resource."
}

export function SearchExperience({ resources }: SearchExperienceProps) {
  const router = useRouter()
  const [filters, setFilters] = React.useState<FiltersState>({ query: "", category: "all" })
  const [currentPage, setCurrentPage] = React.useState(1)

  const enrichedResources = React.useMemo<EnrichedResource[]>(
    () =>
      resources.map((resource) => {
        const category = (deriveCategory(resource) || "Resource").trim() || "Resource"
        const normalizedCategory = category.toLowerCase()

        return {
          ...resource,
          category,
          normalizedCategory,
          tags: deriveTags(resource),
          summary: deriveSummary(resource),
        }
      }),
    [resources],
  )

  const categories = React.useMemo<CategoryOption[]>(() => {
    const map = new Map<string, string>()

    for (const resource of enrichedResources) {
      if (!resource.normalizedCategory) continue
      if (!map.has(resource.normalizedCategory)) {
        map.set(resource.normalizedCategory, resource.category)
      }
    }

    const sorted = Array.from(map.entries()).sort(([, labelA], [, labelB]) => labelA.localeCompare(labelB))

    return [
      { value: "all", label: "All categories" },
      ...sorted.map(([value, label]) => ({ value, label })),
    ]
  }, [enrichedResources])

  const filteredResources = React.useMemo(() => {
    const normalizedQuery = filters.query.trim().toLowerCase()
    return enrichedResources.filter((resource) => {
      const matchesCategory = filters.category === "all" || resource.normalizedCategory === filters.category
      if (!normalizedQuery) return matchesCategory

      const haystack = [
        resource.title,
        resource.summary,
        resource.category,
        resource.authors.join(" "),
        resource.tags.join(" "),
      ]
        .join(" ")
        .toLowerCase()

      return matchesCategory && haystack.includes(normalizedQuery)
    })
  }, [filters, enrichedResources])

  const totalPages = React.useMemo(() => {
    const pages = Math.ceil(filteredResources.length / PAGE_SIZE)
    return pages > 0 ? pages : 1
  }, [filteredResources.length])

  React.useEffect(() => {
    setCurrentPage(1)
  }, [filters.query, filters.category])

  React.useEffect(() => {
    setCurrentPage((previous) => Math.min(previous, totalPages))
  }, [totalPages])

  const paginatedResources = React.useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE
    return filteredResources.slice(start, start + PAGE_SIZE)
  }, [filteredResources, currentPage])

  const handleSubmit = React.useCallback((event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
  }, [])

  return (
    <div className="space-y-6">
      <Card className="border-border/70">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-xl font-semibold">
            <SearchIcon className="h-5 w-5 text-primary" />
            Discover resources
          </CardTitle>
          <CardDescription>
            Explore curated publications, datasets, and mission reports within space biology.
          </CardDescription>
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
                  placeholder="Search by title, author, DOI, or keyword..."
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
                  <Label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Category
                  </Label>
                  <Select
                    value={filters.category}
                    onValueChange={(value) => setFilters((prev) => ({ ...prev, category: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All categories" />
                    </SelectTrigger>
                    <SelectContent className="max-h-60">
                      <SelectGroup>
                        <SelectLabel>Categories</SelectLabel>
                        <ScrollArea className="h-full max-h-48 w-full">
                          <div className="pr-1">
                            {categories.map((category) => (
                              <SelectItem key={category.value} value={category.value} className="capitalize">
                                {category.label}
                              </SelectItem>
                            ))}
                          </div>
                        </ScrollArea>
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
          <div className="space-y-6">
            <div className="grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
              {paginatedResources.map((resource) => (
                <Card
                  key={resource.slug}
                  className="group flex h-full flex-col overflow-hidden border-border/70 bg-card/70 transition hover:border-primary/60 hover:shadow-lg"
                >
                  <CardHeader className="space-y-3">
                    <div className="flex flex-wrap items-center gap-2 text-xs font-medium text-muted-foreground">
                      <Badge variant="secondary" className="bg-primary/10 text-primary">
                        {resource.category}
                      </Badge>
                      {resource.publicationDate ? <span>{resource.publicationDate}</span> : null}
                    </div>
                    <div className="space-y-2">
                      <CardTitle className="text-lg font-semibold text-foreground">
                        {resource.title}
                      </CardTitle>
                      <CardDescription className="text-sm leading-relaxed text-muted-foreground">
                        {resource.summary}
                      </CardDescription>
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

            {filteredResources.length > PAGE_SIZE ? (
              <div className="flex flex-col items-center justify-between gap-3 rounded-lg border border-border/60 bg-card/50 p-4 sm:flex-row">
                <p className="text-sm text-muted-foreground">
                  Showing {(currentPage - 1) * PAGE_SIZE + 1}–
                  {Math.min(currentPage * PAGE_SIZE, filteredResources.length)} of {filteredResources.length} resources
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    Page {currentPage} of {totalPages}
                  </span>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </Button>
                </div>
              </div>
            ) : null}
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
