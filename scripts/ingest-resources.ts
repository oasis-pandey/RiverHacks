import "dotenv/config"

import fs from "fs/promises"
import path from "path"

import { generateEmbedding } from "@/lib/embeddings"
import { createResourceSlug, upsertResource } from "@/lib/resources"

const DATASET_PATH = path.resolve(process.cwd(), "complete_scrape.json")
const MAX_EMBEDDING_CHARS = 8000
const REQUEST_DELAY_MS = 250

const args = process.argv.slice(2)
const limitArg = args.find((arg) => arg.startsWith("--limit="))
const parsedLimit = limitArg ? Number.parseInt(limitArg.split("=")[1] ?? "", 10) : Number.NaN
const MAX_RECORDS = Number.isFinite(parsedLimit) && parsedLimit > 0 ? parsedLimit : Number.POSITIVE_INFINITY

type ResourceDatasetEntry = {
  row?: Record<string, unknown>
  scrape?: {
    url?: string
    title?: string
    authors?: unknown
    publication_date?: string
    doi?: string
    abstract?: string
    full_text?: string
    paragraphs?: string[]
    sections?: string[]
    key_findings?: string[]
    methodology?: string[]
    objectives?: string[]
    [key: string]: unknown
  }
}

type NormalizedResource = {
  title: string
  url: string
  publicationDate: string | null
  authors: string[]
  abstract: string | null
  content: string | null
  metadata: Record<string, unknown>
  embeddingText: string
}

function normalizeResource(entry: ResourceDatasetEntry): NormalizedResource | null {
  const rawTitle = entry.scrape?.title || (entry.row?.["Title"] as string | undefined) || (entry.row?.["﻿Title"] as string | undefined)
  const rawUrl = entry.scrape?.url || (entry.row?.["Link"] as string | undefined)

  if (!rawTitle || !rawUrl) {
    return null
  }

  const authors = Array.isArray(entry.scrape?.authors)
    ? (entry.scrape?.authors as unknown[]).map((author) => String(author)).filter(Boolean)
    : []

  const keyFindings = Array.isArray(entry.scrape?.key_findings) ? (entry.scrape?.key_findings as string[]) : []
  const objectives = Array.isArray(entry.scrape?.objectives) ? (entry.scrape?.objectives as string[]) : []
  const methodology = Array.isArray(entry.scrape?.methodology) ? (entry.scrape?.methodology as string[]) : []
  const sections = Array.isArray(entry.scrape?.sections) ? (entry.scrape?.sections as string[]) : []
  const paragraphs = Array.isArray(entry.scrape?.paragraphs) ? (entry.scrape?.paragraphs as string[]) : []

  const abstract = entry.scrape?.abstract ? String(entry.scrape.abstract) : null
  const fullText = entry.scrape?.full_text ? String(entry.scrape.full_text) : null

  const embeddingParts = [rawTitle]
  if (abstract) embeddingParts.push(abstract)
  if (keyFindings.length) embeddingParts.push(keyFindings.join("\n"))
  if (objectives.length) embeddingParts.push(objectives.join("\n"))
  if (methodology.length) embeddingParts.push(methodology.join("\n"))
  if (paragraphs.length) embeddingParts.push(paragraphs.slice(0, 20).join("\n"))
  if (fullText) embeddingParts.push(fullText)

  const embeddingText = embeddingParts
    .filter((part) => part && part.trim().length > 0)
    .join("\n\n")
    .slice(0, MAX_EMBEDDING_CHARS)

  if (!embeddingText) {
    return null
  }

  return {
    title: rawTitle.trim(),
    url: rawUrl.trim(),
    publicationDate: entry.scrape?.publication_date ? String(entry.scrape.publication_date) : null,
    authors,
    abstract,
    content: fullText,
    metadata: {
      sections,
      keyFindings,
      objectives,
      methodology,
      doi: entry.scrape?.doi ?? null,
      sourceRow: entry.row ?? null,
    },
    embeddingText,
  }
}

async function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

async function loadDataset(): Promise<ResourceDatasetEntry[]> {
  const raw = await fs.readFile(DATASET_PATH, "utf-8")
  const parsed = JSON.parse(raw)

  if (!Array.isArray(parsed)) {
    throw new Error("Resource dataset must be an array")
  }

  return parsed as ResourceDatasetEntry[]
}

async function main() {
  console.log("[resources] Loading dataset from", DATASET_PATH)
  const dataset = await loadDataset()
  console.log(`[resources] Loaded ${dataset.length} entries${Number.isFinite(MAX_RECORDS) ? ` (processing up to ${MAX_RECORDS})` : ""}`)

  let processed = 0
  let skipped = 0

  for (const entry of dataset) {
    if (processed >= MAX_RECORDS) {
      break
    }
    const normalized = normalizeResource(entry)
    if (!normalized) {
      skipped += 1
      continue
    }

    try {
      const embedding = await generateEmbedding(normalized.embeddingText)

      const slug = createResourceSlug(normalized.title, normalized.url)
      await upsertResource({
        slug,
        title: normalized.title,
        url: normalized.url,
        publicationDate: normalized.publicationDate,
        authors: normalized.authors,
        abstract: normalized.abstract,
        content: normalized.content,
        metadata: normalized.metadata,
        embedding,
      })

      processed += 1
      if (processed % 10 === 0) {
        console.log(`[resources] Processed ${processed} records (skipped ${skipped})`)
      }
    } catch (error) {
      skipped += 1
      console.error(`[resources] Failed to ingest resource: ${normalized.title}`, error)
    }

    await delay(REQUEST_DELAY_MS)
  }

  console.log(`[resources] Ingestion complete. Processed ${processed}, skipped ${skipped}.`)
  process.exit(0)
}

main().catch((error) => {
  console.error("[resources] Ingestion failed:", error)
  process.exit(1)
})
