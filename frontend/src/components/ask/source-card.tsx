import { useState } from "react"
import { ChevronRight } from "lucide-react"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { SourceReference } from "@/api/types"

function relevanceVariant(score: number) {
  if (score >= 0.8) return "default"
  if (score >= 0.5) return "secondary"
  return "outline"
}

interface SourceCardProps {
  source: SourceReference
  index: number
}

export function SourceCard({ source, index }: SourceCardProps) {
  const [open, setOpen] = useState(false)

  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="flex w-full items-center gap-2 rounded-md border px-3 py-2 text-left text-sm hover:bg-accent transition-colors">
        <ChevronRight
          className={cn(
            "h-4 w-4 shrink-0 transition-transform",
            open && "rotate-90",
          )}
        />
        <span className="text-muted-foreground">[{index + 1}]</span>
        <span className="flex-1 truncate font-medium">
          {source.document_title}
        </span>
        <Badge variant={relevanceVariant(source.relevance_score)}>
          {(source.relevance_score * 100).toFixed(0)}%
        </Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 rounded-md border bg-muted/50 px-3 py-2">
          <pre className="whitespace-pre-wrap text-sm text-muted-foreground">
            {source.chunk_text}
          </pre>
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}
