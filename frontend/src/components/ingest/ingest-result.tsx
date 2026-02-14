import { CheckCircle } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { IngestResponse } from "@/api/types"

interface IngestResultProps {
  result: IngestResponse
}

export function IngestResult({ result }: IngestResultProps) {
  const { document: doc, chunks_created } = result

  return (
    <Card>
      <CardHeader className="flex-row items-center gap-2 space-y-0 pb-2">
        <CheckCircle className="h-5 w-5 text-green-500" />
        <CardTitle className="text-base">Document ingested</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">Title</dt>
          <dd className="font-medium">{doc.title}</dd>
          <dt className="text-muted-foreground">Source</dt>
          <dd className="truncate">{doc.source}</dd>
          <dt className="text-muted-foreground">Type</dt>
          <dd>{doc.source_type}</dd>
          <dt className="text-muted-foreground">Chunks created</dt>
          <dd>{chunks_created}</dd>
        </dl>
      </CardContent>
    </Card>
  )
}
