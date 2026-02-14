import { Navigate, Route, Routes } from "react-router-dom"
import { MainLayout } from "@/components/layout/main-layout"
import { AskPage } from "@/pages/ask-page"
import { DocumentsPage } from "@/pages/documents-page"
import { IngestPage } from "@/pages/ingest-page"

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<Navigate to="/ask" replace />} />
        <Route path="ask" element={<AskPage />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="ingest" element={<IngestPage />} />
      </Route>
    </Routes>
  )
}
