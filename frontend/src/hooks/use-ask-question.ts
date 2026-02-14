import { useState, useCallback, useRef, useEffect } from "react"
import { askQuestionStream } from "@/api/questions"
import type { ApiError } from "@/api/client"
import type { SourceReference, ConversationMessage } from "@/api/types"

export interface ConversationTurn {
  question: string
  answer: string
  sources: SourceReference[]
  isPending: boolean
}

export function useAskQuestion() {
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [error, setError] = useState<ApiError | null>(null)
  const turnsRef = useRef<ConversationTurn[]>([])
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => {
      abortRef.current?.abort()
    }
  }, [])

  const ask = useCallback(async (question: string) => {
    setError(null)

    const history: ConversationMessage[] = turnsRef.current
      .filter((t) => !t.isPending)
      .flatMap((t) => [
        { role: "user" as const, content: t.question },
        { role: "assistant" as const, content: t.answer },
      ])

    const newTurn: ConversationTurn = {
      question,
      answer: "",
      sources: [],
      isPending: true,
    }

    const nextTurns = [...turnsRef.current, newTurn]
    turnsRef.current = nextTurns
    setTurns(nextTurns)

    const turnIndex = nextTurns.length - 1
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await askQuestionStream(
        { question, history },
        (chunk) => {
          turnsRef.current = turnsRef.current.map((t, i) =>
            i === turnIndex ? { ...t, answer: t.answer + chunk } : t,
          )
          setTurns([...turnsRef.current])
        },
        (sources) => {
          turnsRef.current = turnsRef.current.map((t, i) =>
            i === turnIndex ? { ...t, sources } : t,
          )
          setTurns([...turnsRef.current])
        },
        controller.signal,
      )
      turnsRef.current = turnsRef.current.map((t, i) =>
        i === turnIndex ? { ...t, isPending: false } : t,
      )
      setTurns([...turnsRef.current])
    } catch (e) {
      if (controller.signal.aborted) return
      turnsRef.current = turnsRef.current.filter((_, i) => i !== turnIndex)
      setTurns([...turnsRef.current])
      setError(e as ApiError)
    } finally {
      if (abortRef.current === controller) {
        abortRef.current = null
      }
    }
  }, [])

  const clearConversation = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    turnsRef.current = []
    setTurns([])
    setError(null)
  }, [])

  const isPending = turns.some((t) => t.isPending)

  return { turns, isPending, error, ask, clearConversation }
}
