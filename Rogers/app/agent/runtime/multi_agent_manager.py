from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspaceKey:
    user_id: int
    workspace_id: str


class MultiAgentManager:
    def __init__(self) -> None:
        self._workspaces: dict[WorkspaceKey, dict] = {}

    def get_workspace(self, *, user_id: int, workspace_id: str) -> dict:
        key = WorkspaceKey(user_id=user_id, workspace_id=workspace_id)
        if key not in self._workspaces:
            self._workspaces[key] = {}
        return self._workspaces[key]
