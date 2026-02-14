import Markdown from "react-markdown"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SourceCard } from "./source-card"
import type { AnswerResponse } from "@/api/types"

interface AnswerDisplayProps {
  answer: AnswerResponse
}

export function AnswerDisplay({ answer }: AnswerDisplayProps) {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Answer</CardTitle>
        </CardHeader>
        <CardContent className="prose prose-neutral max-w-none text-sm">
          <Markdown>{answer.text}</Markdown>
        </CardContent>
      </Card>

      {answer.sources.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">
            Sources ({answer.sources.length})
          </h3>
          {answer.sources.map((source, i) => (
            <SourceCard key={source.chunk_id} source={source} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}
