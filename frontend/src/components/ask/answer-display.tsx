import { BookOpen } from "lucide-react"
import Markdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Popover,
  PopoverTrigger,
  PopoverContent,
} from "@/components/ui/popover"
import { SourceCard } from "./source-card"
import type { SourceReference } from "@/api/types"

interface AnswerDisplayProps {
  text: string
  sources: SourceReference[]
}

export function AnswerDisplay({ text, sources }: AnswerDisplayProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Answer</CardTitle>
      </CardHeader>
      <CardContent className="prose prose-neutral max-w-none text-sm">
        <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
      </CardContent>

      {sources.length > 0 && (
        <div className="flex justify-end px-6 pb-4">
          <Popover>
            <PopoverTrigger asChild>
              <button
                type="button"
                className="cursor-pointer"
              >
                <Badge variant="outline" className="gap-1.5">
                  <BookOpen className="size-3" />
                  {sources.length} {sources.length === 1 ? "source" : "sources"}
                </Badge>
              </button>
            </PopoverTrigger>
            <PopoverContent className="w-[28rem] max-h-80 overflow-y-auto space-y-2 p-3">
              {sources.map((source, i) => (
                <SourceCard key={source.chunk_id} source={source} index={i} />
              ))}
            </PopoverContent>
          </Popover>
        </div>
      )}
    </Card>
  )
}
