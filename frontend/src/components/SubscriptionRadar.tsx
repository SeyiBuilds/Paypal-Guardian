import { useEffect, useState } from "react"
import { Radar, RefreshCw, Repeat } from "lucide-react"
import { api, type RadarResponse } from "@/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

function fmtDate(d: string | null) {
  if (!d) return ""
  const date = new Date(d)
  return isNaN(date.getTime()) ? "" : date.toLocaleDateString(undefined, { month: "short", day: "numeric" })
}

export default function SubscriptionRadar() {
  const [data, setData] = useState<RadarResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  function load() {
    setLoading(true)
    setError("")
    api
      .subscriptionRadar()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false))
  }

  useEffect(load, [])

  const subs = data?.subscriptions ?? []
  const message = error || data?.error

  return (
    <Card>
      <CardHeader>
        <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-primary">
          <Radar className="size-4" />
          Track
        </div>
        <CardTitle className="text-lg">Subscription Radar</CardTitle>
        <CardDescription>Repeat charges found in your last 90 days of PayPal history.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {loading && (
          <div className="space-y-3">
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        )}

        {!loading && message && (
          <Alert variant="destructive">
            <AlertDescription className="break-words">{message}</AlertDescription>
          </Alert>
        )}

        {!loading && !message && subs.length === 0 && (
          <div className="rounded-lg border border-dashed p-6 text-center">
            <p className="text-sm font-medium">No repeat charges yet</p>
            <p className="mt-1 text-xs text-muted-foreground">
              Scanned {data?.transactions_scanned ?? 0} transactions. Sandbox history can lag by a few hours.
            </p>
          </div>
        )}

        {!loading && !message && subs.length > 0 && (
          <ul className="divide-y rounded-lg border">
            {subs.map((s) => (
              <li key={`${s.merchant}-${s.amount}`} className="flex items-center gap-3 p-3">
                <div className="flex size-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                  <Repeat className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{s.merchant}</p>
                  <p className="text-xs text-muted-foreground">
                    {s.charge_count} charges{s.last_charged ? `, last on ${fmtDate(s.last_charged)}` : ""}
                  </p>
                </div>
                <Badge variant="secondary" className="tabular-nums">
                  {s.amount} {s.currency}
                </Badge>
              </li>
            ))}
          </ul>
        )}

        <Button variant="outline" size="sm" className="w-full" onClick={load} disabled={loading}>
          <RefreshCw className={loading ? "animate-spin" : ""} />
          Rescan
        </Button>
      </CardContent>
    </Card>
  )
}
