import { apiPost, ApiError, BASE_URL } from "./client"
import type { AnswerResponse, AskQuestionRequest, SourceReference } from "./types"

export function askQuestion(data: AskQuestionRequest): Promise<AnswerResponse> {
  return apiPost<AnswerResponse>("/ask", data)
}

export async function askQuestionStream(
  data: AskQuestionRequest,
  onText: (chunk: string) => void,
  onSources: (sources: SourceReference[]) => void,
): Promise<void> {
  const response = await fetch(`${BASE_URL}/ask/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try {
      const errorData = await response.json()
      if (typeof errorData.detail === "string") {
        message = errorData.detail
      }
    } catch {
      // keep default message
    }
    throw new ApiError(response.status, message)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split("\n")
    buffer = lines.pop()!
    for (const line of lines) {
      if (!line) continue
      const event = JSON.parse(line)
      if (event.type === "text") onText(event.content)
      else if (event.type === "sources") onSources(event.sources)
    }
  }
}
