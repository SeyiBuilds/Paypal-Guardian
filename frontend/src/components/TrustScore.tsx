import { useState } from "react"
import { Loader2, UserSearch } from "lucide-react"
import { api, type TrustResult } from "@/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

const RISK = {
  low: { badge: "success", text: "text-success", bar: "bg-success", box: "border-success/40 bg-success/5" },
  medium: { badge: "warning", text: "text-warning", bar: "bg-warning", box: "border-warning/40 bg-warning/5" },
  high: { badge: "destructive", text: "text-destructive", bar: "bg-destructive", box: "border-destructive/40 bg-destructive/5" },
} as const

export default function TrustScore() {
  const [email, setEmail] = useState("")
  const [accountAge, setAccountAge] = useState("")
  const [priorTxns, setPriorTxns] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TrustResult | null>(null)
  const [error, setError] = useState("")

  async function handleCheck() {
    setLoading(true)
    setError("")
    setResult(null)
    try {
      setResult(
        await api.trustScore(email, {
          claimed_account_age: accountAge || "unknown",
          prior_transaction_count: priorTxns || "unknown",
        })
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : "Trust check failed")
    } finally {
      setLoading(false)
    }
  }

  const level = result?.result.risk_level
  const style = level ? RISK[level] : null

  return (
    <Card>
      <CardHeader>
        <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-primary">
          <UserSearch className="size-4" />
          Assess
        </div>
        <CardTitle className="text-lg">Pre-Payment Trust Score</CardTitle>
        <CardDescription>Check the risk before you send money to someone new.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Counterparty PayPal email</Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-2">
            <Label htmlFor="age">Account age</Label>
            <Input id="age" placeholder="2 weeks" value={accountAge} onChange={(e) => setAccountAge(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="txns">Prior txns</Label>
            <Input id="txns" placeholder="0" value={priorTxns} onChange={(e) => setPriorTxns(e.target.value)} />
          </div>
        </div>
        <Button className="w-full" onClick={handleCheck} disabled={loading || !email}>
          {loading && <Loader2 className="animate-spin" />}
          {loading ? "Analyzing" : "Check trust score"}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription className="break-all">{error}</AlertDescription>
          </Alert>
        )}

        {result && level && style && (
          <div className={cn("space-y-3 rounded-lg border p-4", style.box)}>
            <div className="flex items-end justify-between">
              <Badge variant={style.badge} className="px-2.5 py-1 text-sm uppercase">
                {level} risk
              </Badge>
              <div className="text-right">
                <span className={cn("text-3xl font-semibold tabular-nums", style.text)}>
                  {result.result.score}
                </span>
                <span className="text-sm text-muted-foreground">/100</span>
              </div>
            </div>
            <Progress value={result.result.score} className="bg-muted" indicatorClassName={style.bar} />
            <p className="text-sm leading-relaxed">{result.result.reasoning}</p>
            <p className="border-t pt-3 text-xs text-muted-foreground">
              <span className="font-medium text-foreground">Recommendation: </span>
              {result.result.recommendation}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
