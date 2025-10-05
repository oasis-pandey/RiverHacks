import { SignUpForm } from "@/components/auth/signup-form"
import { SpaceScene } from "@/components/space-scene"
import Link from "next/link"

export default function SignUpPage() {
  return (
    <div className="relative min-h-full overflow-hidden">
      <SpaceScene />

      <div className="relative z-10 flex min-h-full flex-col items-center justify-center px-6 py-24">
        <div className="w-full max-w-md rounded-xl border border-border bg-card/80 p-8 backdrop-blur-sm shadow-lg">
          <div className="mb-6 text-center">
            <h1 className="mb-2 text-3xl font-bold text-card-foreground">Create Account</h1>
            <p className="text-muted-foreground">Start exploring space biology with AI</p>
          </div>

          <SignUpForm />

          <p className="mt-6 text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link href="/auth/signin" className="text-primary hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
