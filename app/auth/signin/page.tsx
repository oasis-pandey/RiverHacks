import { SignInForm } from "@/components/auth/signin-form"
import { SpaceScene } from "@/components/space-scene"
import { Sparkles } from "lucide-react"
import Link from "next/link"

export default function SignInPage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <SpaceScene />

      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center px-6">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-2">
            <Sparkles className="h-8 w-8 text-primary" />
            <span className="font-mono text-2xl font-bold">SpaceBio</span>
          </Link>
        </div>

        <div className="w-full max-w-md rounded-xl border border-border bg-card/80 p-8 backdrop-blur-sm">
          <div className="mb-6 text-center">
            <h1 className="mb-2 text-3xl font-bold text-card-foreground">Welcome Back</h1>
            <p className="text-muted-foreground">Sign in to continue your space biology journey</p>
          </div>

          <SignInForm />

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link href="/auth/signup" className="text-primary hover:underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </main>
  )
}
