import { useState } from "react"
import { Loader2, ShieldAlert, ShieldCheck } from "lucide-react"
import { api, type VerifyResult } from "@/api"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

export default function VerificationShield() {
  const [orderId, setOrderId] = useState("")
  const [claimText, setClaimText] = useState("")
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<VerifyResult | null>(null)
  const [error, setError] = useState("")

  async function handleVerify() {
    setLoading(true)
    setError("")
    setResult(null)
    try {
      setResult(await api.verifyClaim(claimText, orderId.trim()))
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed")
    } finally {
      setLoading(false)
    }
  }

  const verified = result?.result.verified

  return (
    <Card>
      <CardHeader>
        <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-primary">
          <ShieldCheck className="size-4" />
          Verify
        </div>
        <CardTitle className="text-lg">Verification Shield</CardTitle>
        <CardDescription>
          Paste a claimed payment. We check it against the real PayPal order.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="order-id">PayPal order ID</Label>
          <Input
            id="order-id"
            placeholder="e.g. 1V2397990A538225S"
            value={orderId}
            onChange={(e) => setOrderId(e.target.value)}
            className="font-mono"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="claim">What was claimed</Label>
          <Textarea
            id="claim"
            rows={3}
            placeholder="e.g. I paid the $150 logo invoice"
            value={claimText}
            onChange={(e) => setClaimText(e.target.value)}
          />
        </div>
        <Button className="w-full" onClick={handleVerify} disabled={loading || !orderId || !claimText}>
          {loading && <Loader2 className="animate-spin" />}
          {loading ? "Checking" : "Verify claim"}
        </Button>

        {error && (
          <Alert variant="destructive">
            <AlertDescription className="break-all">{error}</AlertDescription>
          </Alert>
        )}

        {result && (
          <div
            className={cn(
              "space-y-3 rounded-lg border p-4",
              verified ? "border-success/40 bg-success/5" : "border-destructive/40 bg-destructive/5"
            )}
          >
            <div className="flex items-center justify-between gap-2">
              <Badge variant={verified ? "success" : "destructive"} className="gap-1.5 px-2.5 py-1 text-sm">
                {verified ? <ShieldCheck /> : <ShieldAlert />}
                {verified ? "Verified" : "Flagged"}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {result.result.confidence} confidence
              </span>
            </div>
            <p className="text-sm leading-relaxed">{result.result.reasoning}</p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              PayPal status
              <Badge variant="outline" className="font-mono">
                {result.actual_status}
              </Badge>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
