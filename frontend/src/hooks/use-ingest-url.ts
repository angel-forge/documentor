import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ingestUrl } from "@/api/ingest"

export function useIngestUrl() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ingestUrl,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] })
    },
  })
}
