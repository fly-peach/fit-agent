import logging
import fakeredis
from datetime import timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# 默认 TTL：7 天
DEFAULT_TTL_DAYS = 7


class ApiKeyCache:
    """API Key 缓存管理（fakeredis 实现，无外部 Redis 依赖）

    - Key 过期后自动失效
    - ``touch()`` 在有调用时刷新 TTL 为完整 7 天
    """

    def __init__(self, ttl_days: int = DEFAULT_TTL_DAYS):
        self.redis = fakeredis.FakeRedis(decode_responses=True)
        self.ttl = timedelta(days=ttl_days)
        self._prefix = "api_key:"
        logger.info("ApiKeyCache initialized (in-memory storage)")

    def _key(self, user_id: int) -> str:
        return f"{self._prefix}{user_id}"

    def set(self, user_id: int, api_key: str) -> None:
        """设置用户 API Key（TTL 从此刻起 7 天）"""
        key = self._key(user_id)
        self.redis.setex(key, self.ttl, api_key)
        logger.info(f"API Key set for user_id: {user_id}, ttl: {self.ttl}")

    def get(self, user_id: int) -> Optional[str]:
        """获取用户 API Key，已过期返回 None"""
        key = self._key(user_id)
        value = self.redis.get(key)
        if value:
            logger.info(f"API Key found for user_id: {user_id}")
        else:
            logger.warning(f"API Key not found for user_id: {user_id}")
        # 当decode_responses=True时，fakeredis会自动解码为字符串
        return str(value) if value else None

    def delete(self, user_id: int) -> None:
        """删除用户 API Key"""
        key = self._key(user_id)
        self.redis.delete(key)
        logger.info(f"API Key deleted for user_id: {user_id}")

    def touch(self, user_id: int) -> bool:
        """刷新 TTL 为完整 7 天（调用成功后调用）

        Returns:
            bool: Key 存在并刷新成功返回 True，不存在返回 False
        """
        key = self._key(user_id)
        if self.redis.exists(key):
            self.redis.expire(key, self.ttl)
            logger.info(f"API Key TTL refreshed for user_id: {user_id}")
            return True
        logger.warning(f"Failed to refresh TTL: API Key not found for user_id: {user_id}")
        return False

    def has_api_key(self, user_id: int) -> bool:
        """检查用户是否已设置 API Key（未过期）"""
        exists = bool(self.redis.exists(self._key(user_id)))
        logger.debug(f"API Key exists for user_id {user_id}: {exists}")
        return exists


# 单例
api_key_cache = ApiKeyCache()