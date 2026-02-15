import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ingestFile } from "@/api/ingest"

export function useIngestFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      onDuplicate,
      title,
    }: {
      file: File
      onDuplicate: "reject" | "skip" | "replace"
      title?: string
    }) => ingestFile(file, onDuplicate, title),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] })
    },
  })
}
