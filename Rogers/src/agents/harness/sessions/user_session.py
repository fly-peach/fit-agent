"""自定义 JSONSession，将会话存储在 users/{user_id}/sessions/ 下。"""
import os
from agentscope.session import JSONSession


class UserSession(JSONSession):
    """将会话文件存储在 {save_dir}/{user_id}/sessions/{session_id}.json。"""

    def _get_save_path(self, session_id: str, user_id: str) -> str:
        if user_id:
            save_dir = os.path.join(self.save_dir, user_id, "sessions")
            file_name = f"{session_id}.json"
        else:
            save_dir = self.save_dir
            file_name = f"{session_id}.json"
        os.makedirs(save_dir, exist_ok=True)
        return os.path.join(save_dir, file_name)
