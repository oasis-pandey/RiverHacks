"use server"

import { sql } from "./db"
import { cookies } from "next/headers"
import { redirect } from "next/navigation"

export async function signUp(email: string, password: string, name: string) {
  try {
    // In a real app, you'd hash the password with bcrypt
    // For now, we'll use a simple approach (NOT PRODUCTION READY)
    const hashedPassword = Buffer.from(password).toString("base64")

    const result = await sql`
      INSERT INTO public.users (email, name, password_hash, created_at, updated_at)
      VALUES (
        ${email}, 
        ${name}, 
        ${hashedPassword},
        NOW(),
        NOW()
      )
      RETURNING id, email, name
    `

    if (result.length === 0) {
      return { error: "Failed to create user" }
    }

    const user = result[0]

    // Set session cookie
    const cookieStore = await cookies()
    cookieStore.set("user_id", user.id, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 1 week
    })

    return { success: true, user }
  } catch (error) {
    console.error("[v0] Sign up error:", error)
    return { error: "Email already exists or invalid data" }
  }
}

export async function signIn(email: string, password: string) {
  try {
    const hashedPassword = Buffer.from(password).toString("base64")

    const result = await sql`
      SELECT id, email, name
      FROM public.users
      WHERE email = ${email}
      AND password_hash = ${hashedPassword}
    `

    if (result.length === 0) {
      return { error: "Invalid email or password" }
    }

    const user = result[0]

    // Set session cookie
    const cookieStore = await cookies()
    cookieStore.set("user_id", user.id, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7, // 1 week
    })

    return { success: true, user }
  } catch (error) {
    console.error("[v0] Sign in error:", error)
    return { error: "Invalid email or password" }
  }
}

export async function signOut() {
  const cookieStore = await cookies()
  cookieStore.delete("user_id")
  redirect("/")
}

export async function getCurrentUser() {
  try {
    const cookieStore = await cookies()
    const userId = cookieStore.get("user_id")?.value

    if (!userId) {
      return null
    }

    const result = await sql`
      SELECT id, email, name
      FROM public.users
      WHERE id = ${userId}
    `

    return result.length > 0 ? result[0] : null
  } catch (error) {
    console.error("[v0] Get current user error:", error)
    return null
  }
}
