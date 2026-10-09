import { useEffect, useState } from "react"
import { ShieldCheck } from "lucide-react"
import VerificationShield from "@/components/VerificationShield"
import TrustScore from "@/components/TrustScore"
import SubscriptionRadar from "@/components/SubscriptionRadar"
import { Badge } from "@/components/ui/badge"
import { api } from "@/api"
import { cn } from "@/lib/utils"

export default function App() {
  const [online, setOnline] = useState<boolean | null>(null)

  useEffect(() => {
    api.health().then(() => setOnline(true)).catch(() => setOnline(false))
  }, [])

  return (
    <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-4 py-8 sm:px-6 lg:py-12">
      <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-xl border bg-primary/10 text-primary">
            <ShieldCheck className="size-6" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">PayPal Guardian</h1>
            <p className="text-sm text-muted-foreground">
              An AI agent that takes the anxiety out of payments.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline">Sandbox</Badge>
          <Badge variant="outline" className="gap-2">
            <span
              className={cn(
                "size-2 rounded-full",
                online === null && "bg-muted-foreground",
                online === true && "bg-success shadow-[0_0_8px] shadow-success",
                online === false && "bg-destructive shadow-[0_0_8px] shadow-destructive"
              )}
            />
            {online === null ? "Connecting" : online ? "API online" : "API offline"}
          </Badge>
        </div>
      </header>

      <main className="grid flex-1 items-start gap-6 md:grid-cols-2 lg:grid-cols-3">
        <VerificationShield />
        <TrustScore />
        <SubscriptionRadar />
      </main>

      <footer className="mt-10 text-center text-xs text-muted-foreground">
        Built on the PayPal REST API and Groq. Sandbox data only.
      </footer>
    </div>
  )
}
