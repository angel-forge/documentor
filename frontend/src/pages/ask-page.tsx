import { useEffect } from "react"
import { QuestionForm } from "@/components/ask/question-form"
import { AnswerDisplay } from "@/components/ask/answer-display"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { useAskQuestion } from "@/hooks/use-ask-question"

export function AskPage() {
  useEffect(() => {
    document.title = "Ask — DocuMentor"
  }, [])

  const { text, sources, isPending, error, ask } = useAskQuestion()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ask a question</h1>
        <p className="text-muted-foreground">
          Ask anything about the ingested documentation.
        </p>
      </div>

      <QuestionForm
        onSubmit={(question) => ask(question)}
        isPending={isPending}
      />

      {isPending && !text && (
        <div className="space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error.message}</AlertDescription>
        </Alert>
      )}

      {text && <AnswerDisplay text={text} sources={sources} />}
    </div>
  )
}
