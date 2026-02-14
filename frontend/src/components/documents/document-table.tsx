import { ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import type { DocumentResponse } from "@/api/types"

interface DocumentTableProps {
  documents: DocumentResponse[] | undefined
  isLoading: boolean
  offset: number
  limit: number
  onOffsetChange: (offset: number) => void
}

export function DocumentTable({
  documents,
  isLoading,
  offset,
  limit,
  onOffsetChange,
}: DocumentTableProps) {
  const hasNext = (documents?.length ?? 0) === limit
  const hasPrev = offset > 0

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-12 w-full" />
        ))}
      </div>
    )
  }

  if (!documents?.length) {
    return (
      <p className="py-8 text-center text-muted-foreground">
        No documents ingested yet. Go to the Ingest page to add documentation.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead className="hidden md:table-cell">Source</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Chunks</TableHead>
              <TableHead className="hidden sm:table-cell">Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell className="font-medium">{doc.title}</TableCell>
                <TableCell className="hidden max-w-[200px] truncate md:table-cell">
                  {doc.source}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{doc.source_type}</Badge>
                </TableCell>
                <TableCell className="text-right">{doc.chunk_count}</TableCell>
                <TableCell className="hidden sm:table-cell">
                  {new Date(doc.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {offset + 1}–{offset + documents.length}
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOffsetChange(Math.max(0, offset - limit))}
            disabled={!hasPrev}
          >
            <ChevronLeft className="mr-1 h-4 w-4" />
            Previous
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onOffsetChange(offset + limit)}
            disabled={!hasNext}
          >
            Next
            <ChevronRight className="ml-1 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
