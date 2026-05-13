import fakeredis
from datetime import timedelta
from typing import Optional

# 默认 TTL：7 天
DEFAULT_TTL_DAYS = 7


class ApiKeyCache:
    """API Key 缓存管理（fakeredis 实现，无外部 Redis 依赖）

    - Key 过期后自动失效
    - ``touch()`` 在有调用时刷新 TTL 为完整 7 天
    """

    def __init__(self, ttl_days: int = DEFAULT_TTL_DAYS):
        self.redis = fakeredis.FakeRedis()
        self.ttl = timedelta(days=ttl_days)
        self._prefix = "api_key:"

    def _key(self, user_id: int) -> str:
        return f"{self._prefix}{user_id}"

    def set(self, user_id: int, api_key: str) -> None:
        """设置用户 API Key（TTL 从此刻起 7 天）"""
        self.redis.setex(self._key(user_id), self.ttl, api_key)

    def get(self, user_id: int) -> Optional[str]:
        """获取用户 API Key，已过期返回 None"""
        value = self.redis.get(self._key(user_id))
        return value.decode("utf-8") if value else None

    def delete(self, user_id: int) -> None:
        """删除用户 API Key"""
        self.redis.delete(self._key(user_id))

    def touch(self, user_id: int) -> bool:
        """刷新 TTL 为完整 7 天（调用成功后调用）

        Returns:
            bool: Key 存在并刷新成功返回 True，不存在返回 False
        """
        key = self._key(user_id)
        if self.redis.exists(key):
            self.redis.expire(key, self.ttl)
            return True
        return False

    def has_api_key(self, user_id: int) -> bool:
        """检查用户是否已设置 API Key（未过期）"""
        return bool(self.redis.exists(self._key(user_id)))


# 单例
api_key_cache = ApiKeyCache()
