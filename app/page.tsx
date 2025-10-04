import { SpaceScene } from "@/components/space-scene"
import { Button } from "@/components/ui/button"
import { ArrowRight, Sparkles, Brain, Rocket } from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <SpaceScene />

      <div className="relative z-10">
        <nav className="flex items-center justify-between px-6 py-6 lg:px-12">
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-primary" />
            <span className="font-mono text-xl font-bold">SpaceBio</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/signin">
              <Button variant="ghost" className="text-foreground">
                Sign In
              </Button>
            </Link>
            <Link href="/auth/signup">
              <Button className="bg-primary text-primary-foreground hover:bg-primary/90">Get Started</Button>
            </Link>
          </div>
        </nav>

        <div className="container mx-auto px-6 py-20 lg:py-32">
          <div className="mx-auto max-w-4xl text-center">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-4 py-2 text-sm text-primary">
              <Sparkles className="h-4 w-4" />
              <span>AI-Powered Space Biology Knowledge</span>
            </div>

            <h1 className="mb-6 text-balance font-sans text-5xl font-bold leading-tight tracking-tight lg:text-7xl">
              Explore the Universe of{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                Space Biology
              </span>
            </h1>

            <p className="mb-10 text-pretty text-lg text-muted-foreground lg:text-xl">
              Your intelligent companion for understanding life beyond Earth. Ask questions, explore research, and
              discover the fascinating intersection of biology and space exploration.
            </p>

            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link href="/auth/signup">
                <Button size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
                  Start Exploring
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="#features">
                <Button size="lg" variant="outline" className="border-border text-foreground bg-transparent">
                  Learn More
                </Button>
              </Link>
            </div>
          </div>

          <div id="features" className="mx-auto mt-32 grid max-w-5xl gap-8 md:grid-cols-3">
            <div className="rounded-xl border border-border bg-card/50 p-6 backdrop-blur-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold text-card-foreground">AI-Powered Insights</h3>
              <p className="text-muted-foreground">
                Get intelligent answers to your space biology questions powered by advanced AI models trained on
                scientific research.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card/50 p-6 backdrop-blur-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-secondary/10">
                <Rocket className="h-6 w-6 text-secondary" />
              </div>
              <h3 className="mb-2 text-xl font-semibold text-card-foreground">Explore Research</h3>
              <p className="text-muted-foreground">
                Access curated knowledge about astrobiology, space medicine, and life in extreme environments.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-card/50 p-6 backdrop-blur-sm">
              <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-lg bg-accent/10">
                <Sparkles className="h-6 w-6 text-accent" />
              </div>
              <h3 className="mb-2 text-xl font-semibold text-card-foreground">Interactive Learning</h3>
              <p className="text-muted-foreground">
                Engage in conversations, save your discoveries, and build your personal space biology knowledge base.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
