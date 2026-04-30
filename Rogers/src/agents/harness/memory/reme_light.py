"""基于 ReMeLight 的记忆管理器，用于 Rogers agent。

封装 ReMeLight 提供对话压缩、语义搜索和记忆摘要功能。
移植自 CoPaw 的 ReMeLightMemoryManager。
"""
import importlib.metadata
import logging
import os
import platform
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from agentscope.agent import ReActAgent
from agentscope.formatter import FormatterBase
from agentscope.message import Msg, TextBlock
from agentscope.model import ChatModelBase
from agentscope.tool import Toolkit, ToolResponse

if TYPE_CHECKING:
    from reme.memory.file_based.reme_in_memory_memory import ReMeInMemoryMemory

from src.agents.config import load_agent_config
from src.agents.harness.utils.token_counter import get_token_counter

logger = logging.getLogger(__name__)

_EXPECTED_REME_VERSION = "0.3.1.8"
_REME_STORE_VERSION = "v1"


class ReMeLightMemoryManager:
    """封装 ReMeLight 的记忆管理器，通过组合模式为 agent 提供服务。

    功能：
    - 通过 compact_memory() 进行对话压缩
    - 通过 memory_search() 进行向量 + 全文搜索
    """

    def __init__(self, working_dir: str, agent_id: str):
        """初始化 ReMeLight 记忆管理器。

        Args:
            working_dir: 记忆存储的工作目录。
            agent_id: Agent 标识符（通常为用户 ID）。
        """
        self.working_dir = working_dir
        self.agent_id = agent_id
        self.chat_model: ChatModelBase | None = None
        self.formatter: FormatterBase | None = None

        self._reme_version_ok = self._check_reme_version()
        self._reme = None

        logger.info(
            f"ReMeLightMemoryManager init: "
            f"agent_id={agent_id}, working_dir={working_dir}",
        )

        # 后端选择（auto：Windows 使用 local，Linux 使用 chroma）
        backend_env = os.environ.get("MEMORY_STORE_BACKEND", "auto")
        if backend_env == "auto":
            if platform.system() == "Windows":
                memory_backend = "local"
            else:
                try:
                    import chromadb  # noqa: F401
                    memory_backend = "chroma"
                except Exception:
                    logger.warning(
                        "chromadb import failed, falling back to local backend"
                    )
                    memory_backend = "local"
        else:
            memory_backend = backend_env

        from reme.reme_light import ReMeLight

        emb_config = self._get_embedding_config()
        vector_enabled = bool(emb_config["base_url"]) and bool(
            emb_config["model_name"],
        )

        log_cfg = {
            **emb_config,
            "api_key": self._mask_key(emb_config["api_key"]),
        }
        logger.info(
            f"Embedding config: {log_cfg}, vector_enabled={vector_enabled}",
        )

        fts_enabled = os.environ.get("FTS_ENABLED", "true").lower() == "true"

        agent_config = load_agent_config(self.agent_id)
        rebuild_on_start = (
            agent_config.running.memory_summary.rebuild_memory_index_on_start
        )

        effective_rebuild = self._resolve_rebuild_on_start(
            working_dir=working_dir,
            store_version=_REME_STORE_VERSION,
            rebuild_on_start=rebuild_on_start,
        )

        recursive_file_watcher = (
            agent_config.running.memory_summary.recursive_file_watcher
        )

        self._reme = ReMeLight(
            working_dir=working_dir,
            default_embedding_model_config=emb_config,
            default_file_store_config={
                "backend": memory_backend,
                "store_name": "memory",
                "vector_enabled": vector_enabled,
                "fts_enabled": fts_enabled,
            },
            default_file_watcher_config={
                "rebuild_index_on_start": effective_rebuild,
                "recursive": recursive_file_watcher,
            },
        )

        # 空工具集 — Rogers 没有 read_file/write_file/edit_file
        self.summary_toolkit = Toolkit()

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _mask_key(key: str) -> str:
        return key[:5] + "*" * (len(key) - 5) if len(key) > 5 else key

    @staticmethod
    def _resolve_rebuild_on_start(
        working_dir: str,
        store_version: str,
        rebuild_on_start: bool,
    ) -> bool:
        sentinel_name = f".reme_store_{store_version}"
        sentinel_path = Path(working_dir) / sentinel_name

        if sentinel_path.exists():
            return rebuild_on_start

        logger.info(f"Sentinel '{sentinel_name}' not found, forcing rebuild.")

        try:
            for old in Path(working_dir).glob(".reme_store_*"):
                old.unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to remove old sentinels: {e}")

        try:
            sentinel_path.touch()
        except Exception as e:
            logger.warning(f"Failed to create sentinel '{sentinel_name}': {e}")

        return True

    @staticmethod
    def _check_reme_version() -> bool:
        try:
            installed = importlib.metadata.version("reme-ai")
        except importlib.metadata.PackageNotFoundError:
            return True
        if installed != _EXPECTED_REME_VERSION:
            logger.warning(
                f"reme-ai version mismatch: installed={installed}, "
                f"expected={_EXPECTED_REME_VERSION}. "
                f"Run `pip install reme-ai=={_EXPECTED_REME_VERSION}`"
            )
            return False
        return True

    def _warn_if_version_mismatch(self) -> None:
        if not self._reme_version_ok:
            logger.warning(
                f"reme-ai version mismatch, expected={_EXPECTED_REME_VERSION}"
            )

    def _prepare_model_formatter(self) -> None:
        """如果未设置，则从已附加的 agent 延迟获取 model/formatter。"""
        self._warn_if_version_mismatch()
        if self.chat_model is None or self.formatter is None:
            # 尝试从缓存的 agent 实例获取 model
            from src.agents.agent import agent_cache
            agent = agent_cache._agents.get(self.agent_id)
            if agent and hasattr(agent, "model") and hasattr(agent, "formatter"):
                self.chat_model = agent.model
                self.formatter = agent.formatter
            else:
                logger.warning(
                    "Could not resolve chat_model/formatter for compaction; "
                    "compaction will fall back to LLM defaults if available."
                )

    def _get_embedding_config(self) -> dict:
        cfg = load_agent_config(self.agent_id).running.embedding_config
        return {
            "backend": cfg.backend,
            "api_key": cfg.api_key or os.environ.get("EMBEDDING_API_KEY", ""),
            "base_url": cfg.base_url or os.environ.get("EMBEDDING_BASE_URL", ""),
            "model_name": cfg.model_name or os.environ.get("EMBEDDING_MODEL_NAME", ""),
            "dimensions": cfg.dimensions,
            "enable_cache": cfg.enable_cache,
            "use_dimensions": cfg.use_dimensions,
            "max_cache_size": cfg.max_cache_size,
            "max_input_length": cfg.max_input_length,
            "max_batch_size": cfg.max_batch_size,
        }

    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    async def start(self):
        if self._reme is None:
            return None
        return await self._reme.start()

    async def close(self) -> bool:
        if self._reme is None:
            return True
        result = await self._reme.close()
        logger.info(f"ReMeLightMemoryManager closed: result={result}")
        return result

    # ------------------------------------------------------------------
    # 对话压缩
    # ------------------------------------------------------------------

    async def compact_tool_result(self, **kwargs):
        if self._reme is None:
            return None
        return await self._reme.compact_tool_result(**kwargs)

    async def check_context(self, **kwargs):
        if self._reme is None:
            return None
        return await self._reme.check_context(**kwargs)

    async def compact_memory(
        self,
        messages: list[Msg],
        previous_summary: str = "",
        extra_instruction: str = "",
        **_kwargs,
    ) -> str:
        """将消息压缩为精简摘要。"""
        self._prepare_model_formatter()
        agent_config = load_agent_config(self.agent_id)
        cc = agent_config.running.context_compact

        kwargs = {
            "messages": messages,
            "as_llm": self.chat_model,
            "as_llm_formatter": self.formatter,
            "as_token_counter": get_token_counter(agent_config),
            "language": "zh",
            "max_input_length": agent_config.running.max_input_length,
            "compact_ratio": cc.memory_compact_ratio,
            "previous_summary": previous_summary,
            "return_dict": True,
            "add_thinking_block": cc.compact_with_thinking_block,
        }
        if extra_instruction:
            kwargs["extra_instruction"] = extra_instruction

        try:
            result = await self._reme.compact_memory(**kwargs)
        except Exception as e:
            logger.error(f"compact_memory failed: {e}")
            return ""

        if isinstance(result, str):
            logger.error(
                "compact_memory returned str instead of dict. "
                "Please upgrade reme package."
            )
            return result

        if not result.get("is_valid", True):
            unique_id = uuid.uuid4().hex[:8]
            filepath = os.path.join(
                self.working_dir,
                f"compact_invalid_{unique_id}.json",
            )
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    import json
                    json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return ""

        return result.get("history_compact", "")

    # ------------------------------------------------------------------
    # 记忆搜索
    # ------------------------------------------------------------------

    async def memory_search(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
    ) -> ToolResponse:
        if self._reme is None or not getattr(self._reme, "_started", False):
            return ToolResponse(
                content=[
                    TextBlock(type="text", text="ReMe 未启动，请检查配置"),
                ],
            )
        return await self._reme.memory_search(
            query=query,
            max_results=max_results,
            min_score=min_score,
        )

    def get_in_memory_memory(self, **_kwargs) -> "ReMeInMemoryMemory | None":
        """返回 ReMeInMemoryMemory 实例，用作 agent 内存。"""
        if self._reme is None:
            return None
        return self._reme.get_in_memory_memory(
            as_token_counter=get_token_counter(load_agent_config(self.agent_id)),  # type: ignore[arg-type]
        )
