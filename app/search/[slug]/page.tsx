import Image from "next/image"
import Link from "next/link"
import { notFound } from "next/navigation"
import { ArrowLeft, ExternalLink, Tag } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { spaceResources } from "@/lib/resources"

export function generateStaticParams() {
  return spaceResources.map((resource) => ({ slug: resource.slug }))
}

interface SearchDetailPageProps {
  params: Promise<{ slug: string }>
}

export default async function SearchDetailPage({ params }: SearchDetailPageProps) {
  const { slug } = await params
  const resource = spaceResources.find((item) => item.slug === slug)

  if (!resource) {
    notFound()
  }

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

      <Card className="overflow-hidden border-border/70">
        <div className="relative h-72 w-full bg-muted">
          <Image
            src={resource.image}
            alt={resource.title}
            fill
            className="object-cover"
            sizes="(min-width: 1024px) 800px, 100vw"
            priority
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/20 to-transparent" />
          <div className="absolute bottom-4 left-4 flex items-center gap-2">
            <Badge variant="secondary" className="bg-secondary/80 text-secondary-foreground">
              {resource.category}
            </Badge>
          </div>
        </div>

        <CardHeader className="space-y-3">
          <CardTitle className="text-3xl font-semibold text-foreground">
            {resource.title}
          </CardTitle>
          <CardDescription className="text-base leading-relaxed text-muted-foreground">
            {resource.description}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Tags</h2>
            <div className="flex flex-wrap gap-2">
              {resource.tags.map((tag) => (
                <Badge key={tag} variant="outline" className="flex items-center gap-1 border-border/70 text-xs uppercase">
                  <Tag className="h-3 w-3" />
                  {tag}
                </Badge>
              ))}
            </div>
          </section>

          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">Explore</h2>
            <div className="flex flex-wrap gap-3">
              <Button variant="default" asChild className="gap-2">
                <Link href={resource.url} target="_blank" rel="noopener noreferrer">
                  Visit website
                  <ExternalLink className="h-4 w-4" />
                </Link>
              </Button>
            </div>
          </section>
        </CardContent>
      </Card>
    </main>
  )
}
