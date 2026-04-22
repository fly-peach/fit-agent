# Rogers 智能健身评估与训练管理平台

<p align="center">
  <a href="#english">English</a> |
  <a href="#中文">中文</a>
</p>

---

<a id="english"></a>

## Rogers - Smart Fitness Assessment & Training Platform

> Your personal data, growth tracking, and AI coach — all running locally on your machine.

### What It Does For You

- **Daily logging** — track body metrics, workouts, and nutrition every day
- **Growth visualization** — see your progress through trend charts and period comparisons
- **AI coach** — chat with an AI assistant that understands your photos (food, scale readings) and gives personalized advice
- **Data privacy** — everything runs locally, your health data stays on your computer

### Quick Start

#### Prerequisites

- **Python 3.11+**
- **Node.js 18+**

#### Step 1: Start Backend

```bash
cd Rogers
pip install -e .
# Copy .env.example to .env and add your API key if you want AI features
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

#### Step 2: Start Frontend

```bash
cd webpage
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

#### Windows Users (One-Command Build)

```powershell
# After backend is running, build and serve frontend from backend
powershell -ExecutionPolicy Bypass -File scripts/build-and-copy-web.ps1
```

#### Linux / macOS Users

```bash
# After backend is running, build and serve frontend from backend
bash scripts/build-and-copy-web.sh
```

### AI Coach Setup (Optional)

The AI coach requires a DashScope API key. Without it, all other features work normally.

1. Get an API key from [DashScope](https://dashscope.console.aliyun.com/)
2. Copy `Rogers/.env.example` to `Rogers/.env`
3. Fill in your key:

```env
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen-vl-plus
AGENT_FRAMEWORK=agentscope
```

> **Tip**: `qwen-vl-plus` supports image recognition and is cost-effective. Avoid higher-tier models to control costs.

### Where Your Data Lives

| Data | Location | Uploaded? |
|------|----------|-----------|
| Body metrics, workouts, nutrition | `Rogers/rogers.db` (SQLite) | No |
| AI chat history | `Rogers/rogers.db` (SQLite) | No |
| AI API requests | Sent to DashScope API only when you use AI features | Only your chat input and uploaded images |

### Project Structure

```
fit-agent/
├── Rogers/                  # Backend (FastAPI)
│   ├── app/                 # Application code
│   │   ├── api/             # REST endpoints
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── agent/           # AI coach logic
│   ├── alembic/             # Database migrations
│   ├── tests/               # Backend tests
│   └── rogers.db            # Local SQLite database
├── webpage/                 # Frontend (React + TypeScript)
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── pages/           # Route pages
│   │   └── services/        # API calls
│   └── dist/                # Build output (auto-generated)
├── scripts/                 # Cross-platform build scripts
└── .plan/                   # Development phase plans
```

### Features Detail

| Module | What You Can Do |
|--------|----------------|
| Dashboard | See today's overview at a glance |
| Body Composition | Log and track weight, BMI, body fat trends |
| Daily Metrics | Record workouts and nutrition per day |
| Assessments | Periodic fitness assessments |
| AI Coach | Chat, upload food/scale photos for auto-analysis |
| Auth | Register, login, JWT-based sessions |

### Run Tests

```bash
cd Rogers
pytest -q
```

---

<a id="中文"></a>

## Rogers 智能健身评估与训练管理平台

> 你的个人健康数据管理、成长可视化 + AI 教练助手 —— 全部在本地运行。

### 能帮你做什么

- **每日记录** — 每天记录身体数据、运动计划和营养摄入
- **成长可视化** — 通过趋势图和对比图直观看到阶段变化
- **AI 教练助手** — 上传食物照片自动识别热量，拍照体重秤自动读数，随时对话
- **数据安全** — 全部运行在本地，你的健康数据不会离开你的电脑

### 最快启动方式

#### 前置要求

- **Python 3.11+**
- **Node.js 18+**

#### 第一步：启动后端

```bash
cd Rogers
pip install -e .
# 如需 AI 功能，复制 .env.example 为 .env 并填入 API Key
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

#### 第二步：启动前端

```bash
cd webpage
npm install
npm run dev
```

浏览器打开 `http://localhost:5173` 即可。

#### Windows 用户（一键构建）

```powershell
# 后端启动后，构建前端并集成到后端
powershell -ExecutionPolicy Bypass -File scripts/build-and-copy-web.ps1
```

#### Linux / macOS 用户

```bash
# 后端启动后，构建前端并集成到后端
bash scripts/build-and-copy-web.sh
```

### AI 教练配置（可选）

AI 教练需要 DashScope API Key。不配置时所有其他功能正常运行。

1. 从 [DashScope](https://dashscope.console.aliyun.com/) 获取 API Key
2. 复制 `Rogers/.env.example` 为 `Rogers/.env`
3. 填入你的 Key：

```env
DASHSCOPE_API_KEY=your-api-key
DASHSCOPE_MODEL=qwen-vl-plus
AGENT_FRAMEWORK=agentscope
```

> **提示**：`qwen-vl-plus` 支持图片识别且价格实惠。避免使用更高模型以控制成本。

### 你的数据存储在哪里

| 数据 | 存储位置 | 是否上传 |
|------|----------|----------|
| 身体数据、运动记录、营养记录 | `Rogers/rogers.db`（SQLite 本地数据库） | 否 |
| AI 聊天记录 | `Rogers/rogers.db`（SQLite 本地数据库） | 否 |
| AI API 请求 | 仅在使用 AI 功能时发送到 DashScope | 仅你的聊天内容和上传图片 |

### 项目结构

```
fit-agent/
├── Rogers/                  # 后端（FastAPI）
│   ├── app/                 # 应用代码
│   │   ├── api/             # REST 接口
│   │   ├── models/          # 数据库模型
│   │   ├── schemas/         # Pydantic 数据模型
│   │   └── agent/           # AI 教练逻辑
│   ├── alembic/             # 数据库迁移
│   ├── tests/               # 后端测试
│   └── rogers.db            # 本地 SQLite 数据库
├── webpage/                 # 前端（React + TypeScript）
│   ├── src/
│   │   ├── components/      # UI 组件
│   │   ├── pages/           # 路由页面
│   │   └── services/        # API 调用
│   └── dist/                # 构建产物（自动生成）
├── scripts/                 # 跨平台构建脚本
└── .plan/                   # 各阶段开发计划
```

### 功能一览

| 模块 | 你能做什么 |
|------|-----------|
| 仪表盘 | 一眼看到今日概览 |
| 体成分 | 记录体重、BMI、体脂，查看趋势 |
| 每日记录 | 按天记录运动和营养 |
| 评估 | 阶段性健身评估 |
| AI 教练 | 对话、上传食物/体重秤照片自动分析 |
| 认证 | 注册、登录、JWT 会话 |

### 运行测试

```bash
cd Rogers
pytest -q
```

### 关键文档

| 文档 | 说明 |
|------|------|
| `Specification.md` | 项目规范（分层、接口约定、智能体规范） |
| `Agent.md` | 协作导航（文档入口、工程结构、协作流程） |
| `.plan/phase-*.md` | 各阶段开发计划 |
