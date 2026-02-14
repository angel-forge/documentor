import { useEffect } from "react"
import { QuestionForm } from "@/components/ask/question-form"
import { AnswerDisplay } from "@/components/ask/answer-display"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { useAskQuestion } from "@/hooks/use-ask-question"
import type { ApiError } from "@/api/client"

export function AskPage() {
  useEffect(() => {
    document.title = "Ask — DocuMentor"
  }, [])

  const mutation = useAskQuestion()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Ask a question</h1>
        <p className="text-muted-foreground">
          Ask anything about the ingested documentation.
        </p>
      </div>

      <QuestionForm
        onSubmit={(question) => mutation.mutate({ question })}
        isPending={mutation.isPending}
      />

      {mutation.isPending && (
        <div className="space-y-3">
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      )}

      {mutation.error && (
        <Alert variant="destructive">
          <AlertDescription>
            {(mutation.error as ApiError).message}
          </AlertDescription>
        </Alert>
      )}

      {mutation.data && <AnswerDisplay answer={mutation.data} />}
    </div>
  )
}
