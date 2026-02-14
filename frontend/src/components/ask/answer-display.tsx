import Markdown from "react-markdown"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SourceCard } from "./source-card"
import type { SourceReference } from "@/api/types"

interface AnswerDisplayProps {
  text: string
  sources: SourceReference[]
}

export function AnswerDisplay({ text, sources }: AnswerDisplayProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Answer</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-neutral max-w-none text-sm">
          <Markdown>{text}</Markdown>
        </CardContent>
      </Card>

      {sources.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">
            Sources ({sources.length})
          </h3>
          {sources.map((source, i) => (
            <SourceCard key={source.chunk_id} source={source} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
