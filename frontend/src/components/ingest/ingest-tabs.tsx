import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { UrlForm } from "./url-form"
import { FileForm } from "./file-form"
import { IngestResult } from "./ingest-result"
import { useIngestUrl } from "@/hooks/use-ingest-url"
import { useIngestFile } from "@/hooks/use-ingest-file"
import type { ApiError } from "@/api/client"

export function IngestTabs() {
  const urlMutation = useIngestUrl()
  const fileMutation = useIngestFile()

  return (
    <Tabs defaultValue="url" className="space-y-4">
      <TabsList>
        <TabsTrigger value="url">From URL</TabsTrigger>
        <TabsTrigger value="file">Upload file</TabsTrigger>
      </TabsList>

      <TabsContent value="url" className="space-y-4">
        <UrlForm
          onSubmit={(source, onDuplicate, title) =>
            urlMutation.mutate({ source, title, on_duplicate: onDuplicate })
          }
          isPending={urlMutation.isPending}
          error={(urlMutation.error as ApiError) ?? null}
        />
        {urlMutation.data && <IngestResult result={urlMutation.data} />}
      </TabsContent>

      <TabsContent value="file" className="space-y-4">
        <FileForm
          onSubmit={(file, onDuplicate, title) =>
            fileMutation.mutate({ file, onDuplicate, title })
          }
          isPending={fileMutation.isPending}
          error={(fileMutation.error as ApiError) ?? null}
        />
        {fileMutation.data && <IngestResult result={fileMutation.data} />}
      </TabsContent>
    </Tabs>
  )
}
