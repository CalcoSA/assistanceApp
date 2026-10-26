from abc import ABC, abstractmethod


class IObjectStorage(ABC):
    """Object paths are relative to the configured application environment prefix."""

    @abstractmethod
    def upload(self, relativePath: str, content: bytes, contentType: str) -> int:
        """Create a new object and return its generation; never overwrite."""
        pass

    @abstractmethod
    def exists(self, relativePath: str) -> bool:
        pass

    @abstractmethod
    def download(self, relativePath: str) -> bytes:
        """Read a private object using backend credentials."""
        pass

    @abstractmethod
    def generateReadUrl(
        self, relativePath: str, expiresInSeconds: int = 300,
        *, fileName: str | None = None, download: bool = False,
    ) -> str:
        pass

    @abstractmethod
    def delete(self, relativePath: str, *, expectedGeneration: int | None = None) -> bool:
        """Delete this object, optionally only its expected generation; False if missing."""
        pass
