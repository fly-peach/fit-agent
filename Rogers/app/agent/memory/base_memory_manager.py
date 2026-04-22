from __future__ import annotations

from typing import Protocol


class BaseMemoryManager(Protocol):
    def maybe_store_user_memory(self, *, user_id: int, message: str) -> bool:
        ...

    def search(self, *, user_id: int, query: str, top_k: int = 5) -> list[str]:
        ...

    def build_context(self, *, user_id: int, query: str, top_k: int = 5) -> str:
        ...
