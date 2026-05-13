# FitAgent - AI 健身管理平台

AI 驱动的健身管理平台，帮你制定训练计划、记录饮食、追踪健康数据，并提供智能对话助手。

## 功能

- **健康追踪** — 记录体重、体脂、BMI，查看趋势变化
- **训练管理** — 创建训练计划，追踪完成进度，获取 AI 推荐
- **饮食记录** — 记录每餐营养，自动计算热量与宏量营养素
- **AI 助手** — 智能对话，回答健身问题，提供个性化建议

## 项目结构

```
fitagent/
├── Rogers/              # 后端 (FastAPI + SQLAlchemy + AgentScope)
│   ├── app/             #   FastAPI 应用、路由、启动逻辑
│   │   ├── main.py      #   入口、中间件、路由注册、静态文件
│   │   ├── routers/     #   API 路由
│   │   └── seed.py      #   测试账户种子
│   ├── src/
│   │   ├── fitme/       #   核心业务层
│   │   │   ├── core/    #     全局配置、数据库连接
│   │   │   ├── models/  #     SQLAlchemy ORM 模型
│   │   │   ├── schemas/ #     Pydantic 请求/响应
│   │   │   ├── services/#     业务逻辑服务
│   │   │   └── seed.py  #     种子数据导入
│   │   └── agents/      #   AI Agent 管道
│   ├── scripts/         #   数据库初始化脚本 & 种子数据
│   ├── data/            #   SQLite 数据库（.gitignore）
│   └── run.py           #   后端启动入口
├── console/             # 前端 (React + TypeScript + Vite)
│   └── src/
│       ├── pages/       # 仪表盘、健康、训练、饮食等
│       ├── services/    # API 客户端
│       └── components/  # AI 助手、动作选择器等
├── mobile/              # 移动端 (React Native + Expo)
│   └── src/screens/     # 认证、聊天、饮食、健康、训练
└── design/              # 设计稿（.pen 文件）
```

## 快速开始

### 1. 后端

```bash
cd Rogers
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env，填入必填项
python run.py
```

首次启动自动初始化数据库（建表 + 导入 871 个健身动作和 295 条食物数据）。

### 2. 前端

**开发模式:**

```bash
cd console
npm install
npm run dev      # → http://localhost:3000
```

**生产构建（嵌入后端）:**

```bash
cd Rogers
python scripts/build_console.py
# 访问 http://localhost:8000 即可使用
```

### 3. 移动端

```bash
cd mobile
npm install
npx expo start
```

## 配置

`.env` 配置项：

| 变量 | 说明 | 必填 |
|------|------|------|
| `JWT_SECRET_KEY` | JWT 签名密钥（`python -c "import secrets; print(secrets.token_hex(32))"`） | **是** |
| `CORS_ORIGINS` | 允许的跨域域名，逗号分隔 | **是** |
| `DASHSCOPE_MODEL` | 默认模型（turbo / plus / max） | 否 |
| `OPENAI_BASE_URL` / `OPENAI_MODEL` | OpenAI 兼容接口 | 否 |

**API Key 通过前端「Agent 配置」页面填入**，每个用户使用自己的 Key。

### 模型参考

| 模型 | 速度 | 精度 | 适用场景 |
|------|------|------|----------|
| qwen-turbo | 快 | 中 | 日常对话 |
| qwen-plus | 中 | 高 | 复杂问题 |
| qwen-max | 慢 | 高 | 专业分析 |

## 测试账户

首次启动自动创建：

```
邮箱: user@test.com
密码: password123
```

## 数据库架构

采用**两库分离**架构，首次启动自动初始化：

| 数据库 | 用途 | 位置 |
|--------|------|------|
| `fitbase.db` | 系统预置数据（动作库、食物库） | `Rogers/data/` |
| `fituser.db` | 用户数据（账户、健康、训练、饮食） | `Rogers/data/` |

### API 路由一览

| 路由组 | 用途 | 主要端点 |
|--------|------|----------|
| `/api/auth` | JWT 认证 | 注册、登录、登出 |
| `/api/user` | 用户信息 | 资料、设置 |
| `/api/health` | 健康追踪 | 体重/体脂/BMI CRUD、报告 |
| `/api/training` | 训练管理 | 计划 CRUD、进度、统计、AI 推荐 |
| `/api/diet` | 饮食记录 | 餐食 CRUD、营养统计、食物库 |
| `/api/exercise` | 动作库 | 检索、分类筛选（只读） |
| `/api/agent/config` | Agent 配置 | API Key 管理 |
| `/agent` | AI 对话 | SSE 流式聊天 |

## Tech Stack

- **后端**: Python 3.10+, FastAPI, SQLAlchemy 2.0, PyJWT
- **AI Agent**: AgentScope Runtime, DashScope LLM
- **前端**: React 18, TypeScript, Vite 5, Ant Design 5, Recharts
- **移动端**: React Native 0.81, Expo 54
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
