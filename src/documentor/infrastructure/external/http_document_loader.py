import asyncio
import socket
from ipaddress import ip_address
from urllib.parse import urlparse

import httpx

from documentor.domain.exceptions import DocumentLoadError
from documentor.domain.models.document import SourceType
from documentor.domain.services.document_loader_service import (
    DocumentLoaderService,
    LoadedDocument,
)


class HttpDocumentLoader(DocumentLoaderService):
    async def load(self, source: str) -> LoadedDocument:
        return await self._load_url(source)

    async def _load_url(self, url: str) -> LoadedDocument:
        await self._validate_url_target(url)
        try:
            async with httpx.AsyncClient(
                timeout=30.0, follow_redirects=False
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = response.text
                title = _extract_title_from_content(content) or _title_from_url(url)
                return LoadedDocument(
                    content=content, title=title, source_type=SourceType.URL
                )
        except DocumentLoadError:
            raise
        except Exception as e:
            raise DocumentLoadError(f"Failed to load URL '{url}': {e}") from e

    async def _validate_url_target(self, url: str) -> None:
        """Reject URLs that resolve to private/reserved IP addresses (SSRF protection)."""
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise DocumentLoadError(f"Invalid URL: no hostname in '{url}'")

        try:
            loop = asyncio.get_running_loop()
            addrinfo = await loop.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise DocumentLoadError(
                f"Cannot resolve hostname '{hostname}'"
            ) from e

        for _family, _type, _proto, _canonname, sockaddr in addrinfo:
            ip = ip_address(sockaddr[0])
            if not ip.is_global:
                raise DocumentLoadError(
                    "URL must not target private or reserved network addresses"
                )


def _extract_title_from_content(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return None


def _title_from_url(url: str) -> str:
    path = url.rstrip("/").split("/")[-1]
    return path.split("?")[0] or url
