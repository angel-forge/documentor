import { apiPost } from "./client"
import type { AnswerResponse, AskQuestionRequest } from "./types"

export function askQuestion(data: AskQuestionRequest): Promise<AnswerResponse> {
  return apiPost<AnswerResponse>("/ask", data)
}
