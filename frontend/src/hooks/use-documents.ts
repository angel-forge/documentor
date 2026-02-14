import { useQuery } from "@tanstack/react-query"
import { listDocuments } from "@/api/documents"

export function useDocuments(offset: number, limit: number) {
  return useQuery({
    queryKey: ["documents", offset, limit],
    queryFn: () => listDocuments(offset, limit),
  })
}
