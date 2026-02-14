import { type FormEvent, useState } from "react"
import { Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface QuestionFormProps {
  onSubmit: (question: string) => void
  isPending: boolean
}

export function QuestionForm({ onSubmit, isPending }: QuestionFormProps) {
  const [question, setQuestion] = useState("")

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const trimmed = question.trim()
    if (!trimmed) return
    onSubmit(trimmed)
    setQuestion("")
  }

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <Input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask a question about the documentation..."
        maxLength={1000}
        disabled={isPending}
        className="flex-1"
      />
      <Button type="submit" disabled={isPending || !question.trim()}>
        {isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
        <span className="ml-1.5 hidden sm:inline">Ask</span>
      </Button>
    </form>
  )
}
