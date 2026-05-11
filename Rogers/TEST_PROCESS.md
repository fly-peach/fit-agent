# /process 接口测试文档

## 接口概述

`POST /process` 是 FitAgent 的核心对话接口，由 AgentScope Runtime 自动注册。该接口处理用户与 AI 助手的对话，支持：

- 文本消息交互
- 图片上传与视觉分析
- 多智能体管道（Pipeline）模式
- 对话历史持久化

## 接口信息

| 项目 | 值 |
|------|-----|
| 路径 | `/process` |
| 方法 | `POST` |
| 认证 | Bearer Token |
| Content-Type | `application/json` |

## 请求格式

### AgentRequest Schema

参考: https://runtime.agentscope.io/en/protocol.html

```python
class AgentRequest(BaseModel):
    input: List[Any]              # 输入消息列表（支持多轮历史）
    session_id: str | None = None # 会话 ID（可选）
    config: dict | None = None    # 配置（可选）
    stream: bool = True           # 是否流式输出（默认 True）
```

### 消息格式 (Msg)

```json
{
  "type": "message",
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "用户消息内容"
    }
  ]
}
```

带图片的消息：

```json
{
  "type": "message",
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "帮我分析这张图片"
    },
    {
      "type": "image",
      "source": {
        "type": "url",
        "url": "/api/agent/images/123"
      }
    }
  ]
}
```

## 前置条件

使用 `/process` 接口前，必须完成以下步骤：

### 1. 登录获取 Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@test.com",
  "password": "password123"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {...}
}
```

### 2. 配置 API Key

```http
PUT /api/agent/config
Authorization: Bearer <token>
Content-Type: application/json

{
  "api_key": "your_api_key_here"
}
```

### 3. 创建会话

```http
POST /api/agent/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "测试会话"
}
```

响应示例：
```json
[
  {
    "id": "1778234255682",
    "name": "测试会话",
    "pinned": false,
    "updated_at": "2024-05-11T10:00:00"
  }
]
```

## 测试用例

### 测试用例 1: 简单文本对话

**描述**: 发送简单的文本消息，获取 AI 回复

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [
        {
          "text": "你好，我是新用户",
          "type": "text"
        }
      ],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期结果**:
- 状态码: `200 OK`
- Content-Type: `text/event-stream` (流式输出) 或 `application/json`
- AI 返回友好的欢迎消息

---

### 测试用例 2: 查询饮食记录

**描述**: 触发饮食数据查询技能

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [
        {
          "text": "我今天的饮食记录怎么样？",
          "type": "text"
        }
      ],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期结果**:
- AI 调用 `fitme-diet` 技能查询数据
- 返回今日营养摄入分析

---

### 测试用例 3: 查询训练记录

**描述**: 触发训练数据查询技能

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [
        {
          "text": "我最近一周的训练情况如何？",
          "type": "text"
        }
      ],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期结果**:
- AI 调用 `fitme-training` 技能查询数据
- 返回训练频率和进度分析

---

### 测试用例 4: 触发 Pipeline 模式 (复杂分析)

**描述**: 请求综合分析，触发多智能体 Fanout 管道

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [
        {
          "text": "帮我全面分析一下最近的饮食和训练情况，给出改进建议",
          "type": "text"
        }
      ],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期流程**:
1. Master Agent 判断任务复杂度
2. 输出 pipeline 标记触发 Fanout
3. DietAnalyst 子 Agent 并行分析饮食
4. TrainingAnalyst 子 Agent 并行分析训练
5. Master Agent 汇总结果，给出综合建议

**预期输出顺序**:
- 🍎 **饮食分析** (DietAnalyst 结果)
- 💪 **训练分析** (TrainingAnalyst 结果)
- Rogers 的综合总结

---

### 测试用例 5: 多轮对话历史

**描述**: 传入完整的对话历史，让 AI 理解上下文

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [{"text": "我今天早餐吃了两个鸡蛋", "type": "text"}],
      "role": "user",
      "type": "message"
    },
    {
      "content": [{"text": "很好！鸡蛋富含优质蛋白质。还吃了别的吗？", "type": "text"}],
      "role": "assistant",
      "type": "message"
    },
    {
      "content": [{"text": "还有一杯牛奶和一片面包，帮我算一下总热量", "type": "text"}],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期结果**:
- AI 基于完整对话历史回复
- 消息自动持久化到 agent_memory.db

---

### 测试用例 6: 带图片的对话 (视觉分析)

**前置步骤**: 先上传图片

```http
POST /api/agent/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: [选择图片文件]
```

获取图片 URL: `{"url": "/api/agent/images/123"}`

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [
    {
      "content": [
        {
          "text": "帮我看看这顿饭营养怎么样",
          "type": "text"
        },
        {
          "type": "image",
          "source": {
            "type": "url",
            "url": "/api/agent/images/123"
          }
        }
      ],
      "role": "user",
      "type": "message"
    }
  ],
  "session_id": "<session_id>"
}
```

**预期流程**:
1. Vision Agent 分析图片内容
2. Master Agent 结合视觉描述和对话继续处理

---

### 测试用例 7: 未登录 (无 Token)

**请求**:
```http
POST /process
Content-Type: application/json

{
  "input": [...],
  "session_id": "<session_id>"
}
```

**预期结果**:
- 状态码: `200 OK` (接口始终返回 200，错误通过消息返回)
- 响应内容: `"请先登录后再使用助手。"`

---

### 测试用例 8: 会话不存在

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [...],
  "session_id": "non-existent-session"
}
```

**预期结果**:
- 响应内容: `"❌ 会话不存在，请先点击「新建对话」创建会话后再发送消息。"`

---

### 测试用例 9: 未配置 API Key

**请求**:
```http
POST /process
Authorization: Bearer <token>
Content-Type: application/json

{
  "input": [...],
  "session_id": "<session_id>"
}
```

**预期结果**:
- 响应内容: `"❌ 请先在「Agent 配置」页面设置 API Key"`

---

## 错误处理

| 场景 | 响应消息 |
|------|----------|
| 未登录 | `"请先登录后再使用助手。"` |
| 会话不存在 | `"❌ 会话不存在，请先点击「新建对话」创建会话后再发送消息。"` |
| 未配置 API Key | `"❌ 请先在「Agent 配置」页面设置 API Key"` |
| 其他错误 | `"❌ <简短错误>\n\n<details>...<\/details>"` |

## 认证方式

支持三种方式传递 Token：

### 1. Authorization Header (推荐)
```http
Authorization: Bearer <token>
```

### 2. Query Parameter (用于 SSE)
```
POST /process?token=<token>
```

### 3. Cookie
```
Cookie: token=<token>
```

## Pipeline 工作流

当启用 Pipeline 模式时，工作流如下：

```
用户消息
    ↓
[Step 1] Vision Agent (如有图片)
    ↓
[Step 2] Master Agent → 判断复杂度
    ↓
    ├─ Simple → 直接回复
    ↓
    └─ Complex → 触发 Fanout
                  ↓
          [Step 3] DietAnalyst + TrainingAnalyst (并行)
                  ↓
          [Step 4] Master Agent 汇总 → 最终回复
```

## 相关接口

| 接口 | 方法 | 用途 |
|------|------|------|
| `/api/auth/login` | POST | 登录获取 Token |
| `/api/agent/config` | GET/PUT | 查看/更新 Agent 配置 |
| `/api/agent/config/status` | GET | 检查配置状态 |
| `/api/agent/sessions` | GET/POST/PUT/DELETE | 会话管理 |
| `/api/agent/upload` | POST | 上传图片 |
| `/api/agent/images/{id}` | GET | 获取图片 |

## Python 测试脚本示例

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. 登录
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "user@test.com", "password": "password123"}
)
token = login_response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 2. 创建会话
session_response = requests.post(
    f"{BASE_URL}/api/agent/sessions",
    headers=headers,
    json={"name": "测试会话"}
)
session_id = session_response.json()[0]["id"]

# 3. 调用 /process
response = requests.post(
    f"{BASE_URL}/process",
    headers=headers,
    json={
        "input": [
            {
                "content": [{"text": "你好！", "type": "text"}],
                "role": "user",
                "type": "message"
            }
        ],
        "session_id": session_id
    },
    stream=True  # 流式输出
)

for line in response.iter_lines():
    if line:
        print(line.decode("utf-8"))
```
