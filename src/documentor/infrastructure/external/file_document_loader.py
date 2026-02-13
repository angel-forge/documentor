from pathlib import PurePosixPath

import pymupdf

from documentor.domain.exceptions import DocumentLoadError
from documentor.domain.models.document import SourceType
from documentor.domain.services.document_loader_service import (
    DocumentLoaderService,
    LoadedDocument,
)

_TEXT_EXTENSIONS = {".txt", ".md", ".html", ".rst"}


class FileDocumentLoader(DocumentLoaderService):
    def __init__(self, file_content: bytes, filename: str) -> None:
        self._file_content = file_content
        self._filename = filename

    async def load(self, source: str) -> LoadedDocument:
        ext = PurePosixPath(self._filename).suffix.lower()

        try:
            if ext == ".pdf":
                content = self._extract_pdf()
            elif ext in _TEXT_EXTENSIONS:
                content = self._file_content.decode("utf-8")
            else:
                raise DocumentLoadError(f"Unsupported file extension: {ext}")
        except DocumentLoadError:
            raise
        except Exception as e:
            raise DocumentLoadError(
                f"Failed to extract content from '{self._filename}': {e}"
            ) from e

        title = _extract_title(content, ext) or PurePosixPath(self._filename).stem

        return LoadedDocument(content=content, title=title, source_type=SourceType.FILE)

    def _extract_pdf(self) -> str:
        doc = pymupdf.open(stream=self._file_content, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()

        return "\n".join(pages)


def _extract_title(content: str, ext: str) -> str | None:
    if ext in (".md", ".rst"):
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    return None
