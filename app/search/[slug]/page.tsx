import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, ExternalLink, Tag } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { listResources, getResourceBySlug } from "@/lib/resources"

export async function generateStaticParams() {
  const resources = await listResources()
  return resources.map((resource) => ({ slug: resource.slug }))
}

interface SearchDetailPageProps {
  params: Promise<{ slug: string }>
}

function ensureArray(value: unknown): string[] {
  if (Array.isArray(value)) {
    return value.map((entry) => String(entry))
  }

  if (typeof value === "string") {
    return [value]
  }

  return []
}

export default async function SearchDetailPage({ params }: SearchDetailPageProps) {
  const { slug } = await params
  const resource = await getResourceBySlug(slug)

  if (!resource) {
    notFound()
  }

  const sections = ensureArray(resource.metadata?.sections)
  const keyFindings = ensureArray(resource.metadata?.keyFindings)
  const objectives = ensureArray(resource.metadata?.objectives)
  const methodology = ensureArray(resource.metadata?.methodology)
  const doi = typeof resource.metadata?.doi === "string" ? (resource.metadata.doi as string) : null

  return (
    <main className="container mx-auto max-w-5xl px-6 pb-16 pt-10 md:px-8 md:pb-20 md:pt-14">
      <div className="mb-6 flex items-center gap-2 text-sm text-muted-foreground">
        <Button variant="ghost" size="sm" asChild className="gap-2 px-3">
          <Link href="/search">
            <ArrowLeft className="h-4 w-4" />
            Back to search
          </Link>
        </Button>
      </div>

      <Card className="border-border/70">
        <CardHeader className="space-y-4 border-b border-border/60 bg-muted/10">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs uppercase tracking-wide text-muted-foreground">
            <div className="flex flex-wrap items-center gap-2">
              {resource.publicationDate ? <span>{resource.publicationDate}</span> : null}
              {doi ? <span>{doi}</span> : null}
            </div>
            <div className="flex flex-wrap gap-2">
              {sections.slice(0, 4).map((section) => (
                <Badge key={section} variant="secondary" className="bg-secondary/80 text-secondary-foreground">
                  {section}
                </Badge>
              ))}
            </div>
          </div>

          <CardTitle className="text-3xl font-semibold text-foreground">
            {resource.title}
          </CardTitle>
          <CardDescription className="text-base leading-relaxed text-muted-foreground">
            {resource.abstract ?? "No abstract available for this resource."}
          </CardDescription>

          <div className="flex flex-wrap gap-2 text-sm text-muted-foreground">
            {resource.authors.length > 0 ? <span>Authors: {resource.authors.join(", ")}</span> : null}
          </div>

          {resource.url ? (
            <div>
              <Button variant="default" asChild className="gap-2">
                <Link href={resource.url} target="_blank" rel="noopener noreferrer">
                  Visit resource
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          ) : null}
        </CardHeader>

        <CardContent className="space-y-8 py-8">
          {keyFindings.length > 0 ? (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                <Tag className="h-4 w-4" /> Key findings
              </h2>
              <ul className="space-y-2 text-sm leading-relaxed text-muted-foreground">
                {keyFindings.map((finding, index) => (
                  <li key={`${finding}-${index}`} className="rounded-md border border-border/50 bg-muted/10 p-3">
                    {finding}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {objectives.length > 0 ? (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Objectives
              </h2>
              <ul className="space-y-2 text-sm leading-relaxed text-muted-foreground">
                {objectives.map((objective, index) => (
                  <li key={`${objective}-${index}`} className="rounded-md border border-border/50 bg-muted/10 p-3">
                    {objective}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {methodology.length > 0 ? (
            <section className="space-y-3">
              <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
                Methodology highlights
              </h2>
              <ul className="space-y-2 text-sm leading-relaxed text-muted-foreground">
                {methodology.map((item, index) => (
                  <li key={`${item}-${index}`} className="rounded-md border border-border/50 bg-muted/10 p-3">
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {resource.content ? (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Full text</h2>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground/90">
                {resource.content}
              </p>
            </section>
          ) : null}
        </CardContent>
      </Card>
    </main>
  )
}
