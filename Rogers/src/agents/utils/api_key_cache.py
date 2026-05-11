import fakeredis
from datetime import timedelta
from typing import Optional


class ApiKeyCache:
    """API Key 会话缓存管理"""

    def __init__(self, ttl_days: int = 5):
        self.redis = fakeredis.FakeRedis()
        self.ttl = timedelta(days=ttl_days)
        self._prefix = "api_key:"

    def set(self, user_id: int, api_key: str) -> None:
        """设置用户 API Key"""
        key = f"{self._prefix}{user_id}"
        self.redis.setex(key, self.ttl, api_key)

    def get(self, user_id: int) -> Optional[str]:
        """获取用户 API Key"""
        key = f"{self._prefix}{user_id}"
        value = self.redis.get(key)
        return value.decode("utf-8") if value else None

    def delete(self, user_id: int) -> None:
        """删除用户 API Key"""
        key = f"{self._prefix}{user_id}"
        self.redis.delete(key)

    def refresh_ttl(self, user_id: int) -> bool:
        """刷新 TTL（用户活跃时调用）"""
        key = f"{self._prefix}{user_id}"
        if self.redis.exists(key):
            self.redis.expire(key, self.ttl)
            return True
        return False

    def has_api_key(self, user_id: int) -> bool:
        """检查用户是否已设置 API Key"""
        key = f"{self._prefix}{user_id}"
        return self.redis.exists(key) > 0


# 单例
api_key_cache = ApiKeyCache()
