/// <reference types="vitest" />

import { describe, expect, it } from "vitest"

import { cn } from "@/lib/utils"

describe("cn helper", () => {
  it("merges conditional class names", () => {
    const result = cn("btn", undefined, { "btn-disabled": false, active: true })

    expect(result).toBe("btn active")
  })

  it("applies Tailwind conflict resolution rules", () => {
    const result = cn("p-2", "bg-blue-500", "p-4")

    expect(result).toBe("bg-blue-500 p-4")
  })
})
