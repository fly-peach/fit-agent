"""Custom JSONSession that stores sessions under users/{user_id}/sessions/."""
import os
from agentscope.session import JSONSession


class UserSession(JSONSession):
    """Store session files at {save_dir}/{user_id}/sessions/{session_id}.json."""

    def _get_save_path(self, session_id: str, user_id: str) -> str:
        if user_id:
            save_dir = os.path.join(self.save_dir, user_id, "sessions")
            file_name = f"{session_id}.json"
        else:
            save_dir = self.save_dir
            file_name = f"{session_id}.json"
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, file_name)
