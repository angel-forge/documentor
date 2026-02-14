import { useEffect, useState } from "react"
import { DocumentTable } from "@/components/documents/document-table"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { useDocuments } from "@/hooks/use-documents"
import type { ApiError } from "@/api/client"

const PAGE_SIZE = 20

export function DocumentsPage() {
  useEffect(() => {
    document.title = "Documents — DocuMentor"
  }, [])

  const [offset, setOffset] = useState(0)
  const { data, isLoading, error } = useDocuments(offset, PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Documents</h1>
        <p className="text-muted-foreground">
          All ingested documentation sources.
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>
            {(error as ApiError).message}
          </AlertDescription>
        </Alert>
      )}

      <DocumentTable
        documents={data}
        isLoading={isLoading}
        offset={offset}
        limit={PAGE_SIZE}
        onOffsetChange={setOffset}
      />
    </div>
  )
}
