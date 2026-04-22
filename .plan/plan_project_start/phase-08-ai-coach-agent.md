| # Phase 08: AI 教练智能体
| > 阶段目标：实现 AI 教练智能体，支持健身问答、训练建议、健康数据分析，以及用户数据编辑（需人工审批）。
| ## 1. 功能范围
| ### 1.1 核心能力
| 能力 | 说明 | 优先级 |
| |------|------|--------|
| **健身问答** | 解答用户关于健身、营养、恢复的问题 | P0 |
| **健康数据分析** | 分析体重、体脂、运动时长趋势 | P0 |
| **训练建议生成** | 基于健康数据生成个性化训练建议 | P1 |
| **数据编辑** | 帮助用户修改每日记录数据（需审批） | P1 |
| ### 1.2 用户交互
| - **前端 AI 侧边栏**：右侧固定侧边栏，支持对话和审批操作
| - **对话历史**：持久化存储，支持跨会话查看
| - **待审批操作**：敏感操作需用户确认后执行
| ## 2. 技术方案
| ### 2.1 框架选型
| 场景 | 框架 | 理由 |
| |------|------|------|
| 健身问答 | LangChain `create_agent` | 简单对话场景，快速实现 |
| 数据编辑 | LangChain + Middleware | 需要人工审批敏感操作 |
| 多维度分析 | LangGraph（可选） | 多 Agent 协作场景 |
| ### 2.2 Agent 工具定义
| #### 数据读取工具（无需审批）
| ```python
| @tool
| def get_user_profile(user_id: str) -> dict:
| """获取用户基本信息"""
| pass
| @tool
| def get_health_metrics(user_id: str, days: int = 7, metric_type: str = "weight") -> list:
| """获取健康指标趋势"""
| pass
| @tool
| def get_workout_history(user_id: str, days: int = 7) -> list:
| """获取训练历史"""
| pass
| @tool
| def get_nutrition_history(user_id: str, days: int = 7) -> list:
| """获取营养摄入历史"""
| pass
| @tool
| def get_dashboard_summary(user_id: str) -> dict:
| """获取仪表盘摘要"""
| pass
| ```
| #### 数据编辑工具（需人工审批）
| ```python
| @tool
| def update_daily_metrics(user_id: str, record_date: str, data: dict) -> str:
| """更新每日身体数据（需审批）"""
| pass
| @tool
| def update_workout_plan(user_id: str, record_date: str, plan: dict) -> str:
| """更新训练计划（需审批）"""
| pass
| @tool
| def update_nutrition(user_id: str, record_date: str, data: dict) -> str:
| """更新营养摄入（需审批）"""
| pass
| ```
| ### 2.3 Middleware 配置
| ```python
| from langchain.agents.middleware import HumanInTheLoopMiddleware
| approval_middleware = HumanInTheLoopMiddleware(
| interrupt_on={
| "update_daily_metrics": {"allowed_decisions": ["approve", "edit", "reject"]},
| "update_workout_plan": {"allowed_decisions": ["approve", "edit", "reject"]},
| "update_nutrition": {"allowed_decisions": ["approve", "edit", "reject"]}
| }
| )
| ```
| ## 3. 后端实现
| ### 3.1 目录结构
| ```
| Rogers/app/agent/
| ├── __init__.py
| ├── fitness_agent.py       # AI 教练 Agent 主入口
| ├── tools/
| │   ├── __init__.py
| │   ├── read_tools.py      # 数据读取工具
| │   ├── write_tools.py     # 数据编辑工具
| │   └── analysis_tools.py  # 分析工具
| ├── middleware/
| │   ├── __init__.py
| │   ├── approval.py        # 人工审批中间件
| │   └── pii.py             # PII 脱敏中间件
| ├── schemas/
| │   ├── __init__.py
| │   ├── request.py         # 请求 DTO
| │   └── response.py        # 响应 DTO
| └── service/
| ├── __init__.py
| ├── agent_service.py   # Agent 服务层
| └── session_service.py # 会话管理
| ```
| ### 3.2 API 接口
| 接口 | 方法 | 说明 |
| |------|------|------|
| `/api/v1/agent/chat` | POST | 与 AI 教练对话 |
| `/api/v1/agent/chat/stream` | POST | 流式对话（SSE） |
| `/api/v1/agent/approve` | POST | 审批待确认操作 |
| `/api/v1/agent/history` | GET | 获取对话历史 |
| `/api/v1/agent/pending` | GET | 获取待审批操作 |
| ### 3.3 数据模型
| #### Agent 会话表
| ```python
| class AgentSession(Base):
| __tablename__ = "agent_sessions"
| id: Mapped[str] = mapped_column(primary_key=True)
| user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
| created_at: Mapped[datetime]
| updated_at: Mapped[datetime]
| ```
| #### Agent 消息表
| ```python
| class AgentMessage(Base):
| __tablename__ = "agent_messages"
| id: Mapped[str] = mapped_column(primary_key=True)
| session_id: Mapped[str] = mapped_column(ForeignKey("agent_sessions.id"))
| role: Mapped[str]  # user/assistant/tool
| content: Mapped[str]
| tool_calls: Mapped[dict] = mapped_column(nullable=True)
| created_at: Mapped[datetime]
| ```
| #### 待审批操作表
| ```python
| class PendingAction(Base):
| __tablename__ = "pending_actions"
| id: Mapped[str] = mapped_column(primary_key=True)
| session_id: Mapped[str] = mapped_column(ForeignKey("agent_sessions.id"))
| tool_name: Mapped[str]
| tool_args: Mapped[dict]
| description: Mapped[str]
| status: Mapped[str]  # pending/approved/rejected/executed
| created_at: Mapped[datetime]
| executed_at: Mapped[datetime] = mapped_column(nullable=True)
| ```
| ## 4. 前端实现
| ### 4.1 AI 侧边栏组件
| ```
| webpage/src/
| ├── features/
| │   └── ai-coach/
| │       ├── AISidebar.tsx        # 侧边栏主组件
| │       ├── ChatMessageList.tsx  # 对话消息列表
| │       ├── PendingActionCard.tsx # 待审批操作卡片
| │       ├── ChatInput.tsx        # 输入框组件
| │       └── hooks/
| │       │   ├── useAgentChat.ts  # 对话 hook
| │       │   └── usePendingActions.ts # 待审批 hook
| │       └── api/
| │           └── agent.ts         # Agent API
| ```
| ### 4.2 UI 结构
| ```
| ┌─────────────────────────────┐
| │  AI 教练                    │  ← 标题栏
| │  ─────────────────────────  │
| │  [对话消息列表]              │  ← 消息区域
| │  - 用户消息                  │
| │  - AI 回复                  │
| │  - 工具调用结果              │
| │  ─────────────────────────  │
| │  [待审批操作卡片]            │  ← 审批区域
| │  ┌─────────────────────┐    │
| │  │ 更新 2025-04-15 体重 │    │
| │  │ 数据: 85.5kg        │    │
| │  │ [确认] [修改] [拒绝] │    │
| │  └─────────────────────┘    │
| │  ─────────────────────────  │
| │  [输入框] [发送按钮]         │  ← 输入区域
| └─────────────────────────────┘
| ```
| ### 4.3 侧边栏样式
| ```css
| .ai-sidebar {
| position: fixed;
| right: 0;
| top: 0;
| width: 320px;
| height: 100vh;
| background: #fff;
| border-left: 1px solid #e0e0e0;
| z-index: 1000;
| display: flex;
| flex-direction: column;
| }
| .ai-sidebar.collapsed {
| width: 48px;
| }
| .ai-sidebar-toggle {
| position: fixed;
| right: 320px;
| top: 50%;
| transform: translateY(-50%);
| width: 24px;
| height: 48px;
| background: #1890ff;
| border-radius: 4px 0 0 4px;
| cursor: pointer;
| }
| ```
| ### 4.4 状态管理
| ```typescript
| interface AgentState {
| sessionId: string | null;
| messages: ChatMessage[];
| pendingActions: PendingAction[];
| isLoading: boolean;
| isSidebarOpen: boolean;
| }
| const useAgentStore = create<AgentState>((set) => ({
| sessionId: null,
| messages: [],
| pendingActions: [],
| isLoading: false,
| isSidebarOpen: true,
| sendMessage: async (message: string) => { ... },
| approveAction: async (actionId: string, decision: string) => { ... },
| toggleSidebar: () => set((s) => ({ isSidebarOpen: !s.isSidebarOpen })),
| }));
| ```
| ## 5. 任务拆解
| ### 5.1 后端任务
| 任务 | 说明 |
| |------|------|------|
| 创建 agent 目录结构 | 初始化目录和 __init__.py |
| 实现数据读取工具 | get_user_profile, get_health_metrics 等 |
| 实现数据编辑工具 | update_daily_metrics 等 |
| 实现 Agent 服务层 | agent_service.py, session_service.py |
| 实现 API 路由 | agent.py 路由文件 |
| 创建数据模型 | AgentSession, AgentMessage, PendingAction |
| 编写 Alembic 迁移 | 数据库迁移脚本 |
| ### 5.2 前端任务
| 任务 | 说明 |
| |------|------|------|
| 创建 AI 侧边栏组件 | AISidebar.tsx |
| 实现对话消息列表 | ChatMessageList.tsx |
| 实现待审批卡片 | PendingActionCard.tsx |
| 实现输入框组件 | ChatInput.tsx |
| 实现 Agent API | agent.ts |
| 实现 Zustand 状态 | useAgentStore |
| 集成到 AppShell | 在主布局中添加侧边栏 |
| ### 5.3 集成测试
| 任务 | 说明 |
| |------|------|------|
| 对话流程测试 | 用户对话 -> AI 回复 |
| 审批流程测试 | 待审批 -> 确认/拒绝 -> 执行 |
| 数据隔离测试 | 多用户数据隔离验证 |
| ## 6. 验收标准
| ### 6.1 功能验收
| - [ ] 用户可以通过 AI 侧边栏与教练对话
| - [ ] AI 教练可以读取用户健康数据并分析趋势
| - [ ] AI 教练可以生成训练建议
| - [ ] 数据编辑操作需用户审批后执行
| - [ ] 对话历史持久化存储
| - [ ] 多用户数据隔离正确
| ### 6.2 安全验收
| - [ ] 敏感操作必须经过人工审批
| - [ ] 用户健康数据传入 Agent 前脱敏
| - [ ] Agent 对话历史可审计追溯
| - [ ] Agent 不直接写数据库，通过 Tools 调用
| ### 6.3 UI 验收
| - [ ] AI 侧边栏可展开/折叠
| - [ ] 对话消息正确显示（用户/AI/工具）
| - [ ] 待审批操作卡片显示完整信息
| - [ ] 审批按钮（确认/修改/拒绝）功能正常
| ## 7. 依赖与风险
| ### 7.1 依赖
| - LangChain 1.x 库（`pip install langchain langchain-openai`）
| - OpenAI API Key（或其他 LLM 提供商）
| - 现有数据模型（daily_metrics, daily_workout_plan, daily_nutrition）
| ### 7.2 风险
| 风险 | 影响 | 缓解措施 |
| |------|------|----------|
| LLM API 调用延迟 | 用户等待时间长 | 实现流式响应（SSE） |
| Agent 误操作 | 数据被错误修改 | 人工审批 + 操作日志 |
| Token 消耗过大 | 成本增加 | 对话历史摘要 + 限制长度 |
| ## 8. 后续扩展
| - Phase 09：多 Agent 协作（LangGraph）
| - Phase 10：长期记忆与个性化推荐
| - Phase 11：语音对话支持