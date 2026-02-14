import { apiGet } from "./client"
import type { DocumentResponse } from "./types"

export function listDocuments(
  offset: number,
  limit: number,
): Promise<DocumentResponse[]> {
  return apiGet<DocumentResponse[]>(
    `/documents?offset=${offset}&limit=${limit}`,
  )
}
