import { useMutation, useQueryClient } from "@tanstack/react-query"
import { ingestFile } from "@/api/ingest"

export function useIngestFile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      file,
      onDuplicate,
      title,
      language,
    }: {
      file: File
      onDuplicate: "reject" | "skip" | "replace"
      title?: string
      language?: string
    }) => ingestFile(file, onDuplicate, title, language),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] })
    },
  })
}
