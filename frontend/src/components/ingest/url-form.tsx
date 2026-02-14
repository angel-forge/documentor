import { type FormEvent, useState } from "react"
import { Loader2, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import type { ApiError } from "@/api/client"

interface UrlFormProps {
  onSubmit: (source: string, onDuplicate: "reject" | "skip" | "replace") => void
  isPending: boolean
  error: ApiError | null
}

export function UrlForm({ onSubmit, isPending, error }: UrlFormProps) {
  const [url, setUrl] = useState("")
  const [onDuplicate, setOnDuplicate] = useState<"reject" | "skip" | "replace">(
    "reject",
  )

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = url.trim()
    if (!trimmed) return
    onSubmit(trimmed, onDuplicate)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-2">
        <label htmlFor="url" className="text-sm font-medium">
          Documentation URL
        </label>
        <Input
          id="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://docs.example.com/guide"
          type="url"
          disabled={isPending}
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="on-duplicate" className="text-sm font-medium">
          On duplicate
        </label>
        <Select
          value={onDuplicate}
          onValueChange={(v) =>
            setOnDuplicate(v as "reject" | "skip" | "replace")
          }
        >
          <SelectTrigger id="on-duplicate">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="reject">Reject</SelectItem>
            <SelectItem value="skip">Skip</SelectItem>
            <SelectItem value="replace">Replace</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      <Button type="submit" disabled={isPending || !url.trim()}>
        {isPending ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Globe className="mr-1.5 h-4 w-4" />
        )}
        Ingest URL
      </Button>
    </form>
  )
}
