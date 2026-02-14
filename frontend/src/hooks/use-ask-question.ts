import { useState, useCallback } from "react"
import { askQuestionStream } from "@/api/questions"
import type { ApiError } from "@/api/client"
import type { SourceReference } from "@/api/types"

export function useAskQuestion() {
  const [text, setText] = useState("")
  const [sources, setSources] = useState<SourceReference[]>([])
  const [isPending, setIsPending] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const ask = useCallback(async (question: string) => {
    setText("")
    setSources([])
    setError(null)
    setIsPending(true)
    try {
      await askQuestionStream(
        { question },
        (chunk) => setText((prev) => prev + chunk),
        (src) => setSources(src),
      )
    } catch (e) {
      setError(e as ApiError)
    } finally {
      setIsPending(false)
    }
  }, [])

  return { text, sources, isPending, error, ask }
}
