import { SignInForm } from "@/components/auth/signin-form"
import { SpaceScene } from "@/components/space-scene"
import { Sparkles } from "lucide-react"
import Link from "next/link"

export default function SignInPage() {
  return (
    <div className="relative min-h-full overflow-hidden">
      <SpaceScene />

      <div className="relative z-10 flex min-h-full flex-col items-center justify-center px-6 py-24">
        <div className="w-full max-w-md rounded-xl border border-border bg-card/80 p-8 backdrop-blur-sm shadow-lg">
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
    </div>
  )
}
