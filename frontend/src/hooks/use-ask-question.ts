import { useMutation } from "@tanstack/react-query"
import { askQuestion } from "@/api/questions"

export function useAskQuestion() {
  return useMutation({
    mutationFn: askQuestion,
  })
}
