import { apiPost, apiPostForm } from "./client"
import type { IngestResponse, IngestUrlRequest } from "./types"

export function ingestUrl(data: IngestUrlRequest): Promise<IngestResponse> {
  return apiPost<IngestResponse>("/ingest/url", data)
}

export function ingestFile(
  file: File,
  onDuplicate: "reject" | "skip" | "replace",
  title?: string,
): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append("file", file)
  if (title) formData.append("title", title)
  formData.append("on_duplicate", onDuplicate)
  return apiPostForm<IngestResponse>("/ingest/file", formData)
}
