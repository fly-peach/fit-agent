| # Phase 10: 布局解耦与 Agent 对话体验升级
| > 阶段目标：完成三栏布局解耦（左侧导航 / 主内容 / 右侧 Agent），实现滚动互不干扰，并将 Agent 体验升级为对齐 qwenpaw 的多会话、多轮、流式与过程可视化交互。
| ## 1. 需求拆解
| ### 1.1 左侧导航（`aside`）
| - 支持收缩/展开。
| - 收缩后保留图标级导航（或窄栏态），不影响主内容宽度计算。
| - 收缩/展开需平滑过渡，不抖动、不闪烁。
| ### 1.2 主内容区（`main`）
| - `main` 与左右侧边栏滚动独立。
| - 主内容只在自己的容器内滚动，不受 `aside` 或 Agent 区域滚动影响。
| - UI 占位不冲突：任何一侧收缩后，主内容可自适应扩展。
| ### 1.3 Agent 区域
| 1. 收展交互
| - 已有“向右收起”语义保留。
| - 收起后语义反转为“向左展开”。
| - 取消显式 `button` 按钮；改为滑动手势/边缘拖拽收起与展开（鼠标拖拽 + 触屏滑动兼容）。
| 2. 多轮对话与会话结构（参考 CoPaw）
| - Header 新增 Tab：`会话` / `历史对话`。
| - `会话`：当前对话流，支持连续多轮上下文。
| - `历史对话`：历史 session 列表、切换与回放。
| 3. 流式输出与过程可视化
| - 支持流式输出（token 逐段显示）。
| - 展示 thinking 内容（可折叠）。
| - 展示工具调用过程（started/completed/failed、耗时、摘要、结果预览）。
| ## 2. 设计原则
| - 三栏布局使用统一容器管理宽度，避免 fixed 定位导致遮挡。
| - 滚动隔离以容器级 `overflow` 为准，页面根节点不参与业务滚动。
| - Agent 动画采用 transform/translate，不触发主线程重排风暴。
| - 对齐 qwenpaw：信息密度高、状态分层清晰、工具链路可追踪。
| ## 3. 目标架构
| ### 3.1 前端布局架构
| ```text
| AppShell
| ├── LeftNavPanel (可收缩)
| ├── MainViewport (独立滚动容器)
| └── AgentDock (可手势收展，独立滚动容器)
| ```
| 关键状态：
| - `leftNavCollapsed: boolean`
| - `agentDockOpen: boolean`
| - `agentDockWidth: number`（支持拖拽宽度可选）
| - `activeAgentTab: "session" | "history"`
| ### 3.2 Agent UI 架构
| ```text
| AISidebar
| ├── AgentHeaderTabs
| │   ├── 会话
| │   └── 历史对话
| ├── SessionPane
| │   ├── MessageList
| │   ├── ThinkingBlock (可折叠)
| │   ├── ToolCallTimeline
| │   └── PendingActionCard
| ├── HistoryPane
| │   ├── SessionList
| │   └── SessionPreview
| └── ChatInput (文本 + 图片)
| ```
| ### 3.3 流式协议建议
| 本期建议新增流式接口（SSE 优先）：
| - `POST /api/v1/agent/chat/stream`
| - 返回事件流：
| - `message_start`
| - `thinking_delta`
| - `content_delta`
| - `tool_event`
| - `pending_action`
| - `message_end`
| 与现有 `POST /api/v1/agent/chat` 非流式接口并行保留，便于渐进升级。
| ## 4. 参考映射（CoPaw）
| CoPaw 参考 | Rogers 落地 |
| |------|------|
| `console/src/pages/Chat/index.tsx` | `AISidebar` 总装 + 头部动作与能力开关 |
| `components/ChatActionGroup` | Header 操作区（新会话、搜索、历史） |
| `components/ChatHeaderTitle` | 当前会话标题展示 |
| `sessionApi` | Rogers `agent session` 切换与历史回放 |
| `sender.attachments` | Rogers 图片上传入口与预览 |
| ## 5. 实施任务
| ### 5.1 布局与滚动（L 系列）
| 序号 | 任务 | 文件 |
| |------|------|------|
| L1 | AppShell 三栏容器重构（避免 fixed 冲突） | `webpage/src/app/AppShell.tsx` |
| L2 | 左侧导航收缩态（含动画） | `AppShell.tsx`, `styles.css` |
| L3 | 主内容独立滚动与高度约束 | `styles.css` |
| L4 | Agent 区域独立滚动与宽度联动 | `AISidebar.tsx`, `styles.css` |
| ### 5.2 Agent 交互（A 系列）
| 序号 | 任务 | 文件 |
| |------|------|------|
| A1 | 去除收展按钮，改边缘滑动/拖拽交互 | `AISidebar.tsx`, `styles.css` |
| A2 | Header 新增 `会话/历史对话` Tab | `AISidebar.tsx` |
| A3 | 历史会话列表与切换回放 | `shared/api/agent.ts`, `AISidebar.tsx` |
| A4 | 多轮上下文连续对话体验优化 | `AISidebar.tsx` |
| ### 5.3 流式与过程可视化（S 系列）
| 序号 | 任务 | 文件 |
| |------|------|------|
| S1 | 新增流式 chat API 客户端（SSE） | `shared/api/agent.ts` |
| S2 | Message 流式渲染（delta 拼接） | `AISidebar.tsx` |
| S3 | Thinking 区块渲染与折叠 | `AISidebar.tsx`, `styles.css` |
| S4 | ToolCallTimeline 结构化展示 | `AISidebar.tsx`, `styles.css` |
| ### 5.4 后端配套（B 系列）
| 序号 | 任务 | 文件 |
| |------|------|------|
| B1 | 新增 `/agent/chat/stream` SSE 路由 | `Rogers/app/api/v1/agent.py` |
| B2 | AgentService 事件分片输出（thinking/content/tool） | `Rogers/app/agent/service/agent_service.py` |
| B3 | 会话历史接口补充排序与分页参数 | `agent.py`, `agent_repository.py` |
| ## 6. 验收标准
| ### 6.1 布局与滚动验收
| - [ ] 左侧导航可收缩，收缩后主内容宽度自动释放。
| - [ ] `main` 区域滚动独立，左右侧滚动互不影响。
| - [ ] 右侧 Agent 收展不遮挡主内容，不出现重叠/穿透。
| ### 6.2 Agent 交互验收
| - [ ] 取消显式收展按钮，支持边缘滑动/拖拽收展。
| - [ ] Header 包含 `会话/历史对话` Tab，且切换流畅。
| - [ ] 可进行多轮连续对话并保持上下文一致。
| ### 6.3 流式与可视化验收
| - [ ] 回复内容支持流式逐段显示。
| - [ ] thinking 可见且可折叠。
| - [ ] 工具调用过程（开始/完成/失败）可视化展示。
| ## 7. 风险与缓解
| 风险 | 影响 | 缓解措施 |
| |------|------|----------|
| 三栏高度和滚动处理不当 | 出现双滚动/滚动穿透 | 明确容器层级，仅 `main`/`agent` 开启 overflow |
| 手势收展误触 | 体验不稳定 | 设置触发热区阈值与最小滑动距离 |
| SSE 连接中断 | 流式输出中断 | 自动重连 + 回退非流式接口 |
| thinking 与 tool 事件协议不统一 | 前端难渲染 | 统一事件 schema，先文档后实现 |
| ## 8. 里程碑
| - M1（布局完成）：L1-L4
| - M2（Agent 交互完成）：A1-A4
| - M3（流式完成）：S1-S4 + B1-B3
| - M4（联调验收）：全量验收清单通过
| ## 9. 本期不做
| - 不做多 Agent 协作编排（仅单 Agent 会话/历史）。
| - 不做语音流式输入（仅文本与图片）。
| - 不做复杂动画库接入（优先 CSS + 原生手势）。
