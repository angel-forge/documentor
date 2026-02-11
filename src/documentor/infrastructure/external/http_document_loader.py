from pathlib import Path

import httpx

from documentor.domain.exceptions import DocumentLoadError
from documentor.domain.models.document import SourceType
from documentor.domain.services.document_loader_service import (
    DocumentLoaderService,
    LoadedDocument,
)


class HttpDocumentLoader(DocumentLoaderService):
    async def load(self, source: str) -> LoadedDocument:
        if source.startswith(("http://", "https://")):
            return await self._load_url(source)
        return self._load_file(source)

    async def _load_url(self, url: str) -> LoadedDocument:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text
                title = _extract_title_from_content(content) or _title_from_url(url)
                return LoadedDocument(
                    content=content, title=title, source_type=SourceType.URL
                )
        except Exception as e:
            raise DocumentLoadError(f"Failed to load URL '{url}': {e}") from e

    def _load_file(self, path: str) -> LoadedDocument:
        try:
            file_path = Path(path)
            content = file_path.read_text()
            return LoadedDocument(
                content=content,
                title=file_path.stem,
                source_type=SourceType.FILE,
            )
        except Exception as e:
            raise DocumentLoadError(f"Failed to load file '{path}': {e}") from e


def _extract_title_from_content(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _title_from_url(url: str) -> str:
    path = url.rstrip("/").split("/")[-1]
    return path.split("?")[0] or url
