export interface HealthResponse {
  status: string
}

export interface SourceReference {
  document_title: string
  chunk_text: string
  relevance_score: number
  chunk_id: string
}

export interface AnswerResponse {
  text: string
  sources: SourceReference[]
}

export interface DocumentResponse {
  id: string
  source: string
  title: string
  source_type: string
  created_at: string
  chunk_count: number
}

export interface IngestResponse {
  document: DocumentResponse
  chunks_created: number
}

export interface ConversationMessage {
  role: "user" | "assistant"
  content: string
}

export interface AskQuestionRequest {
  question: string
  history?: ConversationMessage[]
}

export interface IngestUrlRequest {
  source: string
  on_duplicate: "reject" | "skip" | "replace"
}

export interface ApiErrorResponse {
  detail: string | Array<{ msg: string; loc: Array<string | number> }>
}
