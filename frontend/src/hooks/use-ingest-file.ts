import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ingestFile } from "@/api/ingest"

export function useIngestFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      onDuplicate,
    }: {
      file: File
      onDuplicate: "reject" | "skip" | "replace"
    }) => ingestFile(file, onDuplicate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] })
    },
  })
}
