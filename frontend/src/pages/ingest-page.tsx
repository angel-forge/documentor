import { useEffect } from "react"
import { IngestTabs } from "@/components/ingest/ingest-tabs"

export function IngestPage() {
  useEffect(() => {
    document.title = "Ingest — DocuMentor"
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Ingest documentation
        </h1>
        <p className="text-muted-foreground">
          Add documentation from a URL or upload a file.
        </p>
      </div>

      <IngestTabs />
    </div>
  )
}
