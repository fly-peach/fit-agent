# Rogers 智能健身评估与训练管理平台

## 1. 项目简介

Rogers 是一个智能健身评估与训练管理平台，定位为"个人用户数据管理与成长可视化应用"，核心价值是帮助用户通过每日记录建立可持续的健康改进闭环：

- **数据记录**：每天记录身体数据、运动计划和营养摄入
- **成长可视化**：通过趋势图和对比图直观看到阶段变化
- **AI 教练助手**：基于 AgentScope + DashScope qwen3.5-plus 的多模态智能教练，支持图片识别（食物、体重秤）、语音输入

## 2. 已完成功能

| Phase | 功能模块 | 状态 |
|-------|----------|------|
| Phase 01 | 用户登录与注册 | ✅ 已完成 |
| Phase 02 | 评估中心基础能力 | ✅ 已完成 |
| Phase 03 | 体成分接入 MVP | ✅ 已完成 |
| Phase 04 | 个人用户看板 MVP | ✅ 已完成 |
| Phase 05 | 每日三记录 + 成长分析 | ✅ 已完成 |
| Phase 06 | 专业仪表盘与健康卡片 | ✅ 已完成 |
| Phase 07 | 每日运动与热量统一页面 | ✅ 已完成 |
| Phase 08 | AI 教练智能体基础 | ✅ 已完成 |
| Phase 09 | AI 教练多模态优化 | ✅ 已完成 |
| Phase 10 | 布局解耦与 Agent 体验升级 | ✅ 已完成 |
| Phase 11 | AgentScope AI 后端重构 | ✅ 已完成 |
| Phase 12 | 流式协议与 UI 消息模型对齐 | ✅ 已完成 |

## 3. 关键文档入口

| 文档 | 说明 |
|------|------|
| `Specification.md` | 项目规范（后端/前端分层、UI 风格、接口约定、智能体规范） |
| `Agent.md` | 协作导航（文档入口、工程结构、协作流程） |
| `.plan/00-project-outline-and-metrics-baseline.md` | 项目大纲与体测数据基线 |
| `.plan/phase-*.md` | 各阶段开发计划 |

## 4. 目录结构

```
fitagent/
├── Rogers/                 # 后端 FastAPI 工程
│   ├── app/
│   │   ├── api/v1/         # API 路由层
│   │   ├── services/       # 业务编排层
│   │   ├── repositories/   # 数据访问层
│   │   ├── models/         # ORM 模型
│   │   ├── schemas/        # Pydantic DTO
│   │   ├── core/           # 配置、安全、日志
│   │   ├── db/             # 数据库会话
│   │   └── agent/          # AI 教练智能体（AgentScope Runtime）
│   │       ├── runtime/            # ReActAgent、模型工厂、流式解析、StreamTracker
│   │       ├── tools/              # 读写工具与定义
│   │       ├── guard/              # Tool Guard + 审批服务
│   │       ├── memory/             # 记忆管理（短期/工作/长期）
│   │       └── service/            # Agent 服务
│   ├── alembic/            # 数据库迁移
│   ├── tests/              # 集成测试
│   └── webpage/            # 前端构建产物
├── webpage/                # 前端 React + Vite 工程
│   └── src/
│       ├── app/            # App 入口与 Shell
│       ├── pages/          # 路由页面
│       ├── router/         # 路由配置
│       ├── shared/         # API、hooks、工具
│       ├── features/       # 业务域组件
│       │   └── ai-coach/   # AI 教练组件（runtime_message_mapper + 分组件渲染）
│       └── store/          # Zustand 状态管理
├── scripts/                # 构建脚本
└── .plan/                  # 阶段开发计划
```

## 5. 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic 2.x |
| 前端 | React 18 + TypeScript + Vite + ECharts + Zustand + Ant Design |
| 数据库 | PostgreSQL（生产）/ SQLite（本地开发） |
| 认证 | JWT（access_token + refresh_token） |
| 智能体 | **AgentScope + DashScope qwen3.5-plus**（多模态：图片、音频、视频） |

### 5.1 AgentScope + DashScope 能力

| 能力 | 说明 |
|------|------|
| **图片理解** | 食物识别、体重秤 OCR、体态分析 |
| **语音识别** | 语音转文字，快速记录数据 |
| **长文本对话** | 128K 上下文，支持复杂对话 |
| **Tool Calling** | AgentScope Toolkit 工具调用，数据读取与编辑 |
| **Guard + Approval** | 工具风险拦截与待审批执行流 |
| **流式协议** | run_id + sequence_number + reconnect，前端统一消息模型驱动渲染 |

## 6. 本地开发快速启动

### 6.1 安装后端依赖

```bash
cd Rogers
pip install -e .
```

### 6.2 配置 AgentScope + DashScope

在 `Rogers/.env` 中配置：

```env
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen3.5-plus
AGENT_FRAMEWORK=agentscope
```

### 6.3 初始化数据库

```bash
cd Rogers
alembic upgrade head
```

### 6.4 启动后端

```bash
cd Rogers
python -m uvicorn app.main:app --reload --port 8000
```

### 6.5 启动前端

```bash
cd webpage
npm install
npm run dev
```

### 6.6 构建前端并复制到后端

**Windows PowerShell:**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-and-copy-web.ps1
```

**Linux/macOS:**
```bash
bash scripts/build-and-copy-web.sh
```

## 7. API 概览

| 模块 | 接口 |
|------|------|
| 认证 | `/api/v1/auth/login`, `/register`, `/refresh`, `/me` |
| 评估 | `/api/v1/assessments`, `/assessments/{id}` |
| 体成分 | `/api/v1/body-composition`, `/body-composition/trend` |
| 每日记录 | `/api/v1/daily-metrics`, `/daily-workout`, `/daily-nutrition` |
| 仪表盘 | `/api/v1/dashboard/me` |
| AI 教练 | `/api/v1/agent/chat`, `/agent/chat/stream`, `/agent/approve`, `/agent/history`, `/agent/pending`, `/agent/sessions` |

## 8. AI 教练多模态功能

### 8.1 支持的输入类型

| 输入类型 | 用途 | 实现方式 |
|----------|------|----------|
| **食物图片** | 自动识别食物，估算热量和营养成分 | AgentScope + qwen3.5-plus 图片理解 |
| **体重秤图片** | 自动读取体重数值 | AgentScope + qwen3.5-plus OCR |
| **语音输入** | 语音转文字，快速记录数据 | AgentScope + qwen3.5-plus 音频理解 |
| **文字输入** | 传统文字对话 | AgentScope ReActAgent 文本对话 |

### 8.2 数据编辑审批流程

敏感操作（修改用户数据）需用户审批：
1. AI 教练识别用户意图
2. 生成待审批操作（展示修改内容）
3. 用户确认/修改/拒绝
4. 执行实际数据更新

### 8.3 流式协议与前端渲染

- **后端**：所有 SSE 事件统一带上 `run_id/session_id/sequence_number/created_at`，支持 `reconnect/run_id/last_seq` 参数回放
- **前端**：`runtime_message_mapper` 统一消息模型驱动渲染，`RuntimeBubbleList/ThinkingCard/ToolCard/OutputCard` 分组件渲染

## 9. 测试

```bash
cd Rogers
pytest -q
```

## 10. 注意事项

- 后端与前端字段命名需保持一致
- 新增接口优先更新 `Specification.md`
- 每个阶段任务以 `.plan` 文档为准
- 智能体敏感操作需人工审批
- AgentScope / DashScope API Key 需配置在 `.env` 中
- `pyproject.toml` 已显式指定 `packages = ["app"]`，避免 setuptools 自动发现多个顶层包