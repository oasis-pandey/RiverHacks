import { createHash } from "crypto"

import { sql } from "./db"

export type Resource = {
  id: string
  slug: string
  title: string
  url: string | null
  publicationDate: string | null
  authors: string[]
  abstract: string | null
  content: string | null
  metadata: Record<string, unknown> | null
  createdAt: string
  updatedAt: string
}

export type UpsertResourceInput = {
  slug: string
  title: string
  url?: string | null
  publicationDate?: string | null
  authors?: string[] | null
  abstract?: string | null
  content?: string | null
  metadata?: Record<string, unknown> | null
  embedding: number[]
}

type ResourceRow = {
  id: string
  slug: string
  title: string
  url: string | null
  publication_date: string | null
  authors: string[] | null
  abstract: string | null
  content: string | null
  metadata: unknown
  created_at: string
  updated_at: string
}

function deserializeResource(row: ResourceRow): Resource {
  let metadata: Record<string, unknown> | null = null

  if (row.metadata) {
    if (typeof row.metadata === "string") {
      try {
        metadata = JSON.parse(row.metadata)
      } catch (error) {
        console.warn("[v0] Failed to parse resource metadata", error)
      }
    } else if (typeof row.metadata === "object") {
      metadata = row.metadata as Record<string, unknown>
    }
  }

  return {
    id: row.id,
    slug: row.slug,
    title: row.title,
    url: row.url,
    publicationDate: row.publication_date,
    authors: row.authors ?? [],
    abstract: row.abstract,
    content: row.content,
    metadata,
    createdAt: row.created_at,
    updatedAt: row.updated_at,
  }
}

export function createResourceSlug(title: string, url?: string | null) {
  const baseSlug = title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 48) || "resource"

  const hashSource = url || title
  const hash = createHash("sha256").update(hashSource).digest("base64url").slice(0, 8)

  return `${baseSlug}-${hash}`
}

export async function listResources(): Promise<Resource[]> {
  const rows = (await sql`
    SELECT id, slug, title, url, publication_date, authors, abstract, content, metadata, created_at, updated_at
    FROM resources
    ORDER BY title ASC
  `) as ResourceRow[]

  return rows.map(deserializeResource)
}

export async function getResourceBySlug(slug: string): Promise<Resource | null> {
  const rows = (await sql`
    SELECT id, slug, title, url, publication_date, authors, abstract, content, metadata, created_at, updated_at
    FROM resources
    WHERE slug = ${slug}
    LIMIT 1
  `) as ResourceRow[]

  if (!rows.length) {
    return null
  }

  return deserializeResource(rows[0])
}

export async function upsertResource(input: UpsertResourceInput): Promise<Resource> {
  const embeddingStr = `[${input.embedding.join(",")}]`

  const rows = (await sql`
    INSERT INTO resources (
      slug,
      title,
      url,
      publication_date,
      authors,
      abstract,
      content,
      metadata,
      embedding,
      updated_at
    ) VALUES (
      ${input.slug},
      ${input.title},
      ${input.url ?? null},
      ${input.publicationDate ?? null},
      ${input.authors ?? null},
      ${input.abstract ?? null},
      ${input.content ?? null},
      ${input.metadata ? JSON.stringify(input.metadata) : null},
      ${embeddingStr}::vector,
      NOW()
    )
    ON CONFLICT (url) DO UPDATE SET
      slug = EXCLUDED.slug,
      title = EXCLUDED.title,
      publication_date = EXCLUDED.publication_date,
      authors = EXCLUDED.authors,
      abstract = EXCLUDED.abstract,
      content = EXCLUDED.content,
      metadata = EXCLUDED.metadata,
      embedding = EXCLUDED.embedding,
      updated_at = NOW()
    RETURNING id, slug, title, url, publication_date, authors, abstract, content, metadata, created_at, updated_at
  `) as ResourceRow[]

  return deserializeResource(rows[0])
}
