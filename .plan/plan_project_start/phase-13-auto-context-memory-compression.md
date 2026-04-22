| # Phase 13: AutoContextMemory 记忆压缩系统
| > 阶段目标：将 Rogers AI Agent 的记忆管理升级为 AgentScope AutoContextMemory 架构，实现四层存储机制、6级渐进式压缩策略、智能摘要与内容卸载，降低 68.4% Token 成本，同时保持完整历史可追溯性。
| ## 1. 改造范围
| ### 1.1 本期必须完成（P0）
| - 建立四层存储架构（Working/Original/Offload/Events）。
| - 实现 6 级渐进式压缩策略（从轻量到重量级）。
| - 集成 LLM 智能摘要能力（历史对话压缩）。
| - 实现大内容卸载与 UUID 按需重载。
| - 保持现有三层记忆兼容（短期/工作/长期）。
| - 完成压缩事件审计日志（可观测性）。
| - 前端支持压缩状态可视化（压缩进度、历史追溯）。
| ### 1.2 本期可选完成（P1）
| - 集成 ReMe 知识图谱增强检索。
| - 支持压缩策略自定义 Prompt（领域优化）。
| - 实现压缩成本统计与优化建议。
| ## 2. 目标架构
| ### 2.1 四层存储架构
| ```text
| ┌─────────────────────────────────────────────┐
| │  1. Working Memory Storage（工作存储）        │
| │     - 存储压缩后的消息                         │
| │     - 用于实际 LLM 对话                       │
| │     - Token 数量受控                          │
| └─────────────────────────────────────────────┘
| ┌─────────────────────────────────────────────┐
| │  2. Original Memory Storage（原始存储）       │
| │     - 存储完整的未压缩历史                     │
| │     - append-only 模式（只追加）              │
| │     - 支持完整历史追溯                         │
| │     - 对应现有 agent_messages 表              │
| └─────────────────────────────────────────────┘
| ┌─────────────────────────────────────────────┐
| │  3. Offload Context Storage（卸载存储）       │
| │     - Map<UUID, List<Msg>>                   │
| │     - 存储卸载的大内容（工具输入/输出）        │
| │     - 按需重新加载                            │
| │     - 新增 agent_offloads 表                  │
| └─────────────────────────────────────────────┘
| ┌─────────────────────────────────────────────┐
| │  4. Compression Events Storage（压缩事件）    │
| │     - 记录所有压缩操作详细信息                 │
| │     - 包括事件类型、时间戳、消息数、token消耗   │
| │     - 新增 agent_compression_events 表        │
| └─────────────────────────────────────────────┘
| ```
| ### 2.2 6 级渐进式压缩策略
| ```text
| 策略 1: 压缩历史工具调用
| - 找到连续工具调用消息（超过 minConsecutiveToolMessages，默认 6）
| - 使用 LLM 智能压缩工具调用历史
| - 保留工具名称、参数、关键结果
| - 保护最新 lastKeep 条消息
| 策略 2: 卸载大消息（带 lastKeep 保护）
| - 找到超过 largePayloadThreshold 的大消息
| - 保护最新 assistant 回复和 lastKeep 条消息
| - 将大内容卸载到外部存储，用 UUID 替代
| - 通过 ContextOffloadTool 按需重载
| 策略 3: 压缩历史对话轮次
| - 找到超过 minConsecutiveRounds 的历史对话轮次
| - 使用 LLM 生成对话摘要
| - 保留关键信息（用户意图、决策、结果）
| - 保护最新 lastKeep 轮对话
| 策略 4: 压缩 Plan 相关消息
| - 识别与当前 Plan 相关的消息
| - 使用最小压缩（仅保留简要描述）
| - 确保 Plan 执行不被中断
| 策略 5: 全局摘要压缩
| - 当前面策略都无法满足 token 限制时
| - 使用 LLM 生成全局对话摘要
| - 包含会话意图、创建的 artifacts、下一步
| 策略 6: 强制截断（最后手段）
| - 当所有策略都无法满足时
| - 强制截断最旧的消息
| - 保留原始存储中的完整历史
| ```
| ### 2.3 压缩触发条件
| ```python
| class AutoContextConfig:
| msg_threshold: int = 30          # 消息数阈值
| token_threshold: int = 100000    # Token 数阈值
| token_ratio: float = 0.3         # Token 占用比例阈值
| last_keep: int = 10              # 保护最新 N 条消息
| min_consecutive_tool_messages: int = 6  # 最小连续工具调用数
| min_consecutive_rounds: int = 5  # 最小连续对话轮次
| large_payload_threshold: int = 5000  # 大消息阈值（字符数）
| ```
| ## 3. 数据库设计
| ### 3.1 新增表结构
| #### agent_offloads（卸载存储）
| ```sql
| CREATE TABLE agent_offloads (
| id VARCHAR(64) PRIMARY KEY,          -- UUID
| session_id VARCHAR(64) NOT NULL,
| user_id INTEGER NOT NULL,
| message_id INTEGER NOT NULL,         -- 关联原始消息
| content_type VARCHAR(32) NOT NULL,   -- 'tool_input' / 'tool_output' / 'large_text'
| content TEXT NOT NULL,               -- 卸载的完整内容
| compressed_summary TEXT,             -- 压缩后的摘要
| created_at TIMESTAMP NOT NULL,
| loaded_at TIMESTAMP,                 -- 最后加载时间
| load_count INTEGER DEFAULT 0         -- 加载次数
| );
| CREATE INDEX idx_offloads_session ON agent_offloads(session_id, user_id);
| CREATE INDEX idx_offloads_message ON agent_offloads(message_id);
| ```
| #### agent_compression_events（压缩事件）
| ```sql
| CREATE TABLE agent_compression_events (
| id SERIAL PRIMARY KEY,
| session_id VARCHAR(64) NOT NULL,
| user_id INTEGER NOT NULL,
| run_id VARCHAR(64) NOT NULL,
| strategy_level INTEGER NOT NULL,     -- 1-6 级策略
| strategy_name VARCHAR(64) NOT NULL,  -- 'compress_tool_calls' / 'offload_large_messages' 等
| messages_before INTEGER NOT NULL,    -- 压缩前消息数
| messages_after INTEGER NOT NULL,     -- 压缩后消息数
| tokens_before INTEGER NOT NULL,      -- 压缩前 token 数
| tokens_after INTEGER NOT NULL,       -- 压缩后 token 数
| compression_ratio FLOAT NOT NULL,    -- 压缩比例
| affected_message_ids TEXT,           -- 受影响的消息 ID 列表（JSON）
| created_at TIMESTAMP NOT NULL
| );
| CREATE INDEX idx_compression_session ON agent_compression_events(session_id, user_id);
| CREATE INDEX idx_compression_run ON agent_compression_events(run_id);
| ```
| ### 3.2 现有表扩展
| #### agent_messages（原始存储）
| ```sql
| -- 新增字段
| ALTER TABLE agent_messages ADD COLUMN is_compressed BOOLEAN DEFAULT FALSE;
| ALTER TABLE agent_messages ADD COLUMN compression_strategy VARCHAR(64);
| ALTER TABLE agent_messages ADD COLUMN offload_id VARCHAR(64);  -- 关联卸载内容
| ALTER TABLE agent_messages ADD COLUMN compressed_summary TEXT;
| ```
| ## 4. 任务拆解
| ### 4.1 存储层任务（S 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| S1 | 创建卸载存储表与 Repository | `models/agent_offload.py`, `repositories/agent_offload_repository.py` |
| S2 | 创建压缩事件表与 Repository | `models/agent_compression_event.py`, `repositories/agent_compression_event_repository.py` |
| S3 | 扩展 agent_messages 表字段 | `models/agent_message.py`, 迁移脚本 |
| S4 | 实现四层存储统一管理器 | `memory/auto_context_storage.py` |
| ### 4.2 压缩策略任务（C 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| C1 | 实现策略 1：压缩历史工具调用 | `memory/compression_strategies/compress_tool_calls.py` |
| C2 | 实现策略 2：卸载大消息 | `memory/compression_strategies/offload_large_messages.py` |
| C3 | 实现策略 3：压缩历史对话轮次 | `memory/compression_strategies/compress_conversation_rounds.py` |
| C4 | 实现策略 4：压缩 Plan 相关消息 | `memory/compression_strategies/compress_plan_messages.py` |
| C5 | 实现策略 5：全局摘要压缩 | `memory/compression_strategies/global_summary.py` |
| C6 | 实现策略 6：强制截断 | `memory/compression_strategies/force_truncate.py` |
| C7 | 实现压缩策略调度器 | `memory/compression_dispatcher.py` |
| ### 4.3 AutoContextMemory 核心任务（A 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| A1 | 实现 AutoContextMemory 主类 | `memory/auto_context_memory.py` |
| A2 | 实现压缩触发检测 | `memory/auto_context_memory.py` |
| A3 | 实现 token 计数与监控 | `memory/token_counter.py` |
| A4 | 实现内容卸载与重载工具 | `tools/context_offload_tool.py` |
| A5 | 集成到 AgentService | `service/agent_service.py` |
| ### 4.4 前端任务（F 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| F1 | 压缩状态可视化组件 | `webpage/src/features/ai-coach/CompressionStatus.tsx` |
| F2 | 历史追溯面板（查看原始历史） | `webpage/src/features/ai-coach/OriginalHistoryPanel.tsx` |
| F3 | 卸载内容加载按钮 | `webpage/src/features/ai-coach/OffloadLoader.tsx` |
| F4 | 压缩事件时间线 | `webpage/src/features/ai-coach/CompressionTimeline.tsx` |
| F5 | API 接口对接 | `webpage/src/shared/api/agent.ts` |
| ### 4.5 API 任务（P 系列）
| 编号 | 任务 | 目标文件 |
| |------|------|------|
| P1 | 新增压缩状态查询接口 | `api/v1/agent.py` |
| P2 | 新增原始历史查询接口 | `api/v1/agent.py` |
| P3 | 新增卸载内容加载接口 | `api/v1/agent.py` |
| P4 | 新增压缩事件查询接口 | `api/v1/agent.py` |
| ## 5. 核心实现示例
| ### 5.1 AutoContextMemory 主类
| ```python
| from typing import List, Dict, Any
| from uuid import uuid4
| class AutoContextMemory:
| def __init__(
| self,
| config: AutoContextConfig,
| model: OpenAIChatModel,
| storage: AutoContextStorage,
| compression_dispatcher: CompressionDispatcher
| ):
| self.config = config
| self.model = model
| self.storage = storage
| self.dispatcher = compression_dispatcher
| self.working_messages: List[Msg] = []
| self.compression_events: List[CompressionEvent] = []
| def add_message(self, msg: Msg) -> None:
| # 添加到工作存储
| self.working_messages.append(msg)
| # 添加到原始存储（append-only）
| self.storage.original.add(msg)
| # 检查是否需要压缩
| if self._should_compress():
| self._compress()
| def _should_compress(self) -> bool:
| # 消息数阈值检查
| if len(self.working_messages) >= self.config.msg_threshold:
| return True
| # Token 数阈值检查
| token_count = self._count_tokens()
| if token_count >= self.config.token_threshold:
| return True
| # Token 占用比例检查
| if token_count / self.model.context_window >= self.config.token_ratio:
| return True
| return False
| def _compress(self) -> None:
| # 按策略级别依次尝试压缩
| for strategy_level in range(1, 7):
| strategy = self.dispatcher.get_strategy(strategy_level)
| result = strategy.compress(
| messages=self.working_messages,
| config=self.config,
| model=self.model,
| storage=self.storage
| )
| if result.success:
| # 记录压缩事件
| event = CompressionEvent(
| id=str(uuid4()),
| session_id=self.session_id,
| strategy_level=strategy_level,
| strategy_name=strategy.name,
| messages_before=result.messages_before,
| messages_after=result.messages_after,
| tokens_before=result.tokens_before,
| tokens_after=result.tokens_after,
| compression_ratio=result.ratio
| )
| self.compression_events.append(event)
| self.storage.events.add(event)
| # 更新工作存储
| self.working_messages = result.compressed_messages
| # 检查是否满足要求
| if not self._should_compress():
| break
| def get_context_for_llm(self) -> List[Msg]:
| # 返回工作存储中的消息（已压缩）
| return self.working_messages
| def get_original_history(self) -> List[Msg]:
| # 返回原始存储中的完整历史
| return self.storage.original.get_all()
| def load_offload_content(self, offload_id: str) -> Dict[str, Any]:
| # 从卸载存储加载内容
| return self.storage.offload.load(offload_id)
| ```
| ### 5.2 压缩策略示例（策略 3：压缩历史对话轮次）
| ```python
| class CompressConversationRoundsStrategy:
| name = "compress_conversation_rounds"
| level = 3
| def compress(
| self,
| messages: List[Msg],
| config: AutoContextConfig,
| model: OpenAIChatModel,
| storage: AutoContextStorage
| ) -> CompressionResult:
| # 找到连续对话轮次
| rounds = self._identify_rounds(messages)
| # 保护最新 lastKeep 轮
| protected_rounds = rounds[-config.last_keep:]
| compressible_rounds = rounds[:-config.last_keep]
| if len(compressible_rounds) < config.min_consecutive_rounds:
| return CompressionResult(success=False, reason="rounds_below_threshold")
| # 使用 LLM 生成摘要
| summary_prompt = self._build_summary_prompt(compressible_rounds)
| summary = model.generate(summary_prompt)
| # 创建摘要消息
| summary_msg = Msg(
| role="system",
| content=f"[历史对话摘要]\n{summary}",
| metadata={"compression_strategy": self.name}
| )
| # 构建压缩后的消息列表
| compressed_messages = [summary_msg] + self._flatten_rounds(protected_rounds)
| # 记录压缩详情
| tokens_before = self._count_tokens(messages)
| tokens_after = self._count_tokens(compressed_messages)
| return CompressionResult(
| success=True,
| compressed_messages=compressed_messages,
| messages_before=len(messages),
| messages_after=len(compressed_messages),
| tokens_before=tokens_before,
| tokens_after=tokens_after,
| ratio=tokens_after / tokens_before
| )
| def _build_summary_prompt(self, rounds: List[List[Msg]]) -> str:
| conversation_text = "\n".join([
| f"用户: {r[0].content}\n助手: {r[1].content}"
| for r in rounds if len(r) >= 2
| ])
| return f"""请将以下历史对话压缩为简洁摘要，保留关键信息：
| {conversation_text}
| 摘要要求：
| 1. 保留用户的核心意图和需求
| 2. 保留助手的关键决策和建议
| 3. 保留重要的数据点和结论
| 4. 使用简洁的语言，不超过 200 字
| 摘要："""
| ```
| ### 5.3 前端压缩状态可视化
| ```tsx
| import React from 'react';
| interface CompressionStatusProps {
| sessionId: string;
| compressionEvents: CompressionEvent[];
| currentTokenCount: number;
| maxTokenLimit: number;
| }
| export function CompressionStatus({
| sessionId,
| compressionEvents,
| currentTokenCount,
| maxTokenLimit
| }: CompressionStatusProps) {
| const latestEvent = compressionEvents[compressionEvents.length - 1];
| const compressionRatio = latestEvent?.compression_ratio ?? 1;
| const savedTokens = latestEvent?.tokens_before - latestEvent?.tokens_after ?? 0;
| return (
| <div className="compression-status">
| <div className="compression-header">
| <h3>记忆压缩状态</h3>
| <span className="compression-badge">
| {compressionRatio < 0.5 ? '高效压缩' : compressionRatio < 0.8 ? '适度压缩' : '轻度压缩'}
| </span>
| </div>
| <div className="compression-metrics">
| <div className="metric-item">
| <label>当前 Token</label>
| <value>{currentTokenCount} / {maxTokenLimit}</value>
| <progress value={currentTokenCount} max={maxTokenLimit} />
| </div>
| <div className="metric-item">
| <label>已节省 Token</label>
| <value>{savedTokens}</value>
| </div>
| <div className="metric-item">
| <label>压缩比例</label>
| <value>{(compressionRatio * 100).toFixed(1)}%</value>
| </div>
| </div>
| <div className="compression-strategies">
| <h4>已执行压缩策略</h4>
| {compressionEvents.map((event, idx) => (
| <div key={idx} className="strategy-item">
| <span className="strategy-level">策略 {event.strategy_level}</span>
| <span className="strategy-name">{event.strategy_name}</span>
| <span className="strategy-result">
| {event.messages_before} → {event.messages_after} 条消息
| </span>
| </div>
| ))}
| </div>
| <button className="view-original-btn" onClick={() => openOriginalHistory(sessionId)}>
| 查看完整原始历史
| </button>
| </div>
| );
| }
| ```
| ## 6. 验收标准
| ### 6.1 功能验收
| - [ ] 四层存储架构完整实现（Working/Original/Offload/Events）。
| - [ ] 6 级压缩策略按序执行，至少触发 1-3 级策略。
| - [ ] 压缩后 Token 数量降低至少 30%（实测目标 68.4%）。
| - [ ] 原始历史完整保留，可通过 API 查询。
| - [ ] 卸载内容可通过 UUID 按需加载。
| - [ ] 压缩事件完整记录，包含策略级别、前后对比、压缩比例。
| - [ ] 前端可查看压缩状态、原始历史、卸载内容。
| - [ ] 压缩不影响对话质量，关键信息不丢失。
| ### 6.2 技术验收
| - [ ] 后端编译通过：`python -m compileall Rogers/app/agent Rogers/app/memory`。
| - [ ] 前端构建通过：`npm run build`（`webpage`）。
| - [ ] 数据库迁移成功：新增表和字段无冲突。
| - [ ] API 接口冒烟通过：
| - `GET /api/v1/agent/compression/status`
| - `GET /api/v1/agent/history/original`
| - `GET /api/v1/agent/offload/{offload_id}`
| - `GET /api/v1/agent/compression/events`
| ### 6.3 性能验收
| - [ ] 压缩触发延迟 < 500ms。
| - [ ] LLM 摘要生成延迟 < 3s。
| - [ ] 卸载内容加载延迟 < 200ms。
| - [ ] 压缩后对话响应时间无明显增加。
| ## 7. 风险与缓解
| 风险 | 影响 | 缓解措施 |
| |------|------|----------|
| 压缩策略误删关键信息 | 对话质量下降 | 原始存储完整保留 + lastKeep 保护最新消息 |
| LLM 摘要质量不稳定 | 信息丢失或冗余 | 摘要 Prompt 优化 + 人工审核样本 |
| 卸载内容加载失败 | 对话中断 | UUID 有效性检查 + 重试机制 |
| Token 计数不准确 | 压缩触发时机错误 | 多种计数方法交叉验证 |
| 压缩事件存储膨胀 | 数据库性能下降 | 定期清理旧事件 + 分页查询 |
| 前端压缩状态展示复杂 | 用户认知负担 | 简化展示 + 默认折叠详情 |
| ## 8. 里程碑
| - M1：存储层完成（S1-S4）
| - M2：压缩策略完成（C1-C7）
| - M3：AutoContextMemory 核心完成（A1-A5）
| - M4：前端可视化完成（F1-F5）
| - M5：API 接口完成（P1-P4）
| - M6：联调验收与性能测试
| ## 9. 本期不做
| - 不引入 ReMe 知识图谱（P1，后续 phase）。
| - 不做多 Agent workspace 隔离（已有 phase-11 规划）。
| - 不做压缩策略 Prompt 自定义（P1，后续优化）。
| - 不做压缩成本统计与优化建议（P1，后续优化）。
| - 不改现有审批流程（pending_actions 仍沿用）。
| ## 10. 参考资源
| - AgentScope AutoContextMemory 文档：https://java.agentscope.io/en/task/memory.html
| - AgentScope 记忆系统架构：https://wayle.blog.csdn.net/article/details/159319931
| - AgentScope Python Memory：https://doc.agentscope.io/tutorial/task_memory.html
| - LangChain ConversationSummaryMemory：https://python.langchain.com.cn/docs/modules/memory/types/summary