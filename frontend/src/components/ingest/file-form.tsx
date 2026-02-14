import { type DragEvent, type FormEvent, useRef, useState } from "react"
import { Loader2, Upload, FileUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import type { ApiError } from "@/api/client"

const ACCEPTED_TYPES = ".txt,.md,.html,.rst,.pdf"

interface FileFormProps {
  onSubmit: (file: File, onDuplicate: "reject" | "skip" | "replace") => void
  isPending: boolean
  error: ApiError | null
}

export function FileForm({ onSubmit, isPending, error }: FileFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [onDuplicate, setOnDuplicate] = useState<"reject" | "skip" | "replace">(
    "reject",
  )
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleDrop(e: DragEvent) {
    e.preventDefault()
    setDragOver(false)
    const dropped = e.dataTransfer.files[0]
    if (dropped) setFile(dropped)
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (!file) return
    onSubmit(file, onDuplicate)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-2 rounded-md border-2 border-dashed p-8 text-center transition-colors",
          dragOver
            ? "border-primary bg-accent"
            : "border-muted-foreground/25 hover:border-muted-foreground/50",
        )}
      >
        <FileUp className="h-8 w-8 text-muted-foreground" />
        {file ? (
          <p className="text-sm font-medium">{file.name}</p>
        ) : (
          <>
            <p className="text-sm font-medium">
              Drop a file here or click to browse
            </p>
            <p className="text-xs text-muted-foreground">
              Accepts .txt, .md, .html, .rst, .pdf
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_TYPES}
          className="hidden"
          onChange={(e) => {
            const selected = e.target.files?.[0]
            if (selected) setFile(selected)
          }}
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="on-duplicate-file" className="text-sm font-medium">
          On duplicate
        </label>
        <Select
          value={onDuplicate}
          onValueChange={(v) =>
            setOnDuplicate(v as "reject" | "skip" | "replace")
          }
        >
          <SelectTrigger id="on-duplicate-file">
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

      <Button type="submit" disabled={isPending || !file}>
        {isPending ? (
          <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
        ) : (
          <Upload className="mr-1.5 h-4 w-4" />
        )}
        Upload file
      </Button>
    </form>
  )
}
