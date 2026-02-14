import { apiPost, apiPostForm } from "./client"
import type { IngestResponse, IngestUrlRequest } from "./types"

export function ingestUrl(data: IngestUrlRequest): Promise<IngestResponse> {
  return apiPost<IngestResponse>("/ingest/url", data)
}

export function ingestFile(
  file: File,
  onDuplicate: "reject" | "skip" | "replace",
): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("on_duplicate", onDuplicate)
  return apiPostForm<IngestResponse>("/ingest/file", formData)
}
