import "dotenv/config"

import { sql } from "../lib/db"
import { generateEmbedding, storeMessageEmbedding } from "../lib/embeddings"

const BATCH_SIZE = 20

async function fetchPendingMessages(limit: number) {
  const rows = await sql`
    SELECT m.id, m.content
    FROM messages m
    LEFT JOIN message_embeddings me ON me.message_id = m.id
    WHERE me.id IS NULL
      AND m.content IS NOT NULL
      AND length(trim(m.content)) > 0
    ORDER BY m.created_at ASC
    LIMIT ${limit}
  `

  return rows as Array<{ id: string; content: string }>
}

async function processBatch() {
  const pending = await fetchPendingMessages(BATCH_SIZE)
  if (pending.length === 0) {
    return false
  }

  console.log(`Processing ${pending.length} messages...`)

  await Promise.all(
    pending.map(async (message) => {
      if (!message.content?.trim()) return

      try {
        const embedding = await generateEmbedding(message.content)
        await storeMessageEmbedding(message.id, embedding)
        console.log(`Embedded message ${message.id}`)
      } catch (error) {
        console.error(`Failed to embed message ${message.id}:`, error)
      }
    }),
  )

  return true
}

async function main() {
  console.log("Starting message embedding backfill...")

  while (await processBatch()) {
    // continue until no pending rows remain
  }

  console.log("Backfill complete.")
  process.exit(0)
}

main().catch((error) => {
  console.error("Backfill script failed:", error)
  process.exit(1)
})
