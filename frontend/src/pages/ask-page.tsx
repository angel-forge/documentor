import { useEffect, useRef } from "react"
import { QuestionForm } from "@/components/ask/question-form"
import { AnswerDisplay } from "@/components/ask/answer-display"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { useAskQuestion } from "@/hooks/use-ask-question"

export function AskPage() {
  useEffect(() => {
    document.title = "Ask — DocuMentor"
  }, [])

  const { turns, isPending, error, ask, clearConversation } = useAskQuestion()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [turns])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between shrink-0 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Ask a question</h1>
          <p className="text-muted-foreground">
            Ask anything about the ingested documentation.
          </p>
        </div>
        {turns.length > 0 && (
          <Button variant="outline" size="sm" onClick={clearConversation}>
            New conversation
          </Button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {turns.map((turn, i) => (
          <div key={i} className="space-y-4">
            <div className="flex justify-end">
              <div className="max-w-[80%] rounded-2xl bg-primary text-primary-foreground px-4 py-2.5 text-sm">
                {turn.question}
              </div>
            </div>

            {turn.isPending && !turn.answer ? (
              <div className="space-y-3">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-2/3" />
              </div>
            ) : (
              turn.answer && (
                <AnswerDisplay text={turn.answer} sources={turn.sources} />
              )
            )}
          </div>
        ))}

        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error.message}</AlertDescription>
          </Alert>
        )}

        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 border-t pt-4">
        <QuestionForm
          onSubmit={(question) => ask(question)}
          isPending={isPending}
        />
      </div>
    </div>
  )
}
