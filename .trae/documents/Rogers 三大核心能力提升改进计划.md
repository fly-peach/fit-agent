# Rogers 三大核心能力提升实施计划

## 总览

本计划专注于实现三个核心能力及其对应前端界面：

1. **Skill 技能系统** - 可插拔的动态能力扩展机制
2. **长期记忆系统** - 从对话压缩升级为状态化长期记忆
3. **上下文生命周期管理** - 四阶段钩子系统

---

## 第一部分：Skill 技能系统

### 1.1 后端实现

#### 文件结构
```
rogers/src/agents/harness/skills/
├── __init__.py
├── skill_manager.py        # Skill 生命周期管理
├── skill_models.py         # Pydantic 数据模型
└── skills/                 # 内置技能目录
    └── example-skill/
        └── SKILL.md
```

#### 实施步骤

**步骤 1: 定义 Skill 数据模型** (`skill_models.py`)

创建以下 Pydantic 模型：
- `SkillMetadata`: name, version, description, author, tags, enabled
- `SkillInfo`: 运行时技能信息（包含内容、路径、状态）
- `SkillConfig`: 技能配置选项（环境变量、依赖项）

SKILL.md 格式规范：
```markdown
---
name: skill-name
version: 1.0.0
description: 简短描述
enabled: true
---

# Skill 名称

## 能力描述
Agent 可以使用此技能做什么。

## 使用指南
如何调用和使用此技能。
```

**步骤 2: 实现 SkillManager** (`skill_manager.py`)

核心功能：
- `scan_skills(working_dir)`: 扫描工作目录下的 skills/ 文件夹
- `load_skill(skill_dir)`: 解析 SKILL.md 并返回 SkillInfo
- `enable_skill(skill_name)`: 启用指定技能
- `disable_skill(skill_name)`: 禁用指定技能
- `get_skill_content(skill_name)`: 获取技能内容注入到 prompt
- `list_skills()`: 返回所有可用技能列表

关键实现细节：
- 使用 frontmatter 库解析 YAML frontmatter
- 技能内容在 Agent 创建时合并到 system prompt
- 支持运行时动态启用/禁用（需要重建 Agent 实例）

**步骤 3: 集成到 Agent 创建流程** (`agent.py`)

修改 `_build_sys_prompt()` 函数：
1. 加载 agents.md + soul.md（现有逻辑）
2. 扫描并加载已启用的 skills/
3. 将技能描述追加到 system prompt 的 "可用能力" 部分
4. 缓存技能列表以便 API 返回

修改 `create_user_agent()` 函数：
- 在初始化 Agent 前调用 `skill_manager.scan_skills()`
- 将技能内容注入到 sys_prompt

**步骤 4: 添加 API 路由** (`app/routers/skills.py`)

端点设计：
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/agent/skills` | 列出所有可用技能 |
| GET | `/api/agent/skills/{name}` | 获取技能详情 |
| PUT | `/api/agent/skills/{name}/enable` | 启用技能 |
| PUT | `/api/agent/skills/{name}/disable` | 禁用技能 |
| POST | `/api/agent/skills/upload` | 上传技能包 (ZIP) |
| DELETE | `/api/agent/skills/{name}` | 删除技能 |

**步骤 5: 更新配置缓存失效**

修改 `update_agent_config` 路由：
- 当 skills 配置变更时调用 `agent_cache.evict(user_id)`
- 确保下次请求使用新技能配置

### 1.2 前端实现

#### 文件结构
```
console/src/
├── pages/
│   └── SkillManager/
│       ├── index.tsx           # 主页面
│       └── components/
│           ├── SkillCard.tsx   # 技能卡片组件
│           └── SkillUpload.tsx # 上传技能组件
├── services/
│   └── skills.ts               # Skill API 服务
```

#### 页面设计

**SkillManager 页面** (`/skills` 路由)

布局结构：
- 顶部：标题 "技能管理" + "上传技能" 按钮
- 主体：技能卡片网格（响应式：桌面 3 列，移动 1 列）
- 每个技能卡片显示：
  - 技能名称、版本、描述
  - 启用/禁用开关（Switch 组件）
  - 查看详情按钮（Modal 弹窗显示完整 SKILL.md）
  - 删除按钮（危险操作确认弹窗）

**SkillCard 组件**:
```
┌─────────────────────────────────┐
│ [图标] Skill Name         v1.0  │
│                                 │
│ 技能描述文本...                 │
│                                 │
│ [标签1] [标签2]                 │
│                                 │
│ [启用开关] [详情] [删除]        │
└─────────────────────────────────┘
```

**SkillUpload 组件**:
- 支持拖拽上传 ZIP 文件
- 上传前校验：文件大小（200MB 限制）、文件类型
- 上传后解析并预览 SKILL.md
- 确认后安装到用户 skills/ 目录

**API 服务** (`services/skills.ts`):
```typescript
export interface Skill {
  name: string;
  version: string;
  description: string;
  enabled: boolean;
  content: string;
  tags?: string[];
}

export const skillApi = {
  list: () => api.get('/agent/skills'),
  get: (name: string) => api.get(`/agent/skills/${name}`),
  enable: (name: string) => api.put(`/agent/skills/${name}/enable`),
  disable: (name: string) => api.put(`/agent/skills/${name}/disable`),
  upload: (file: File) => { /* FormData POST */ },
  delete: (name: string) => api.delete(`/agent/skills/${name}`),
};
```

---

## 第二部分：长期记忆系统

### 2.1 后端实现

#### 文件结构
```
rogers/src/agents/harness/memory/
├── long_term_memory.py     # 长期记忆管理器
└── memory_optimizer.py     # Dream 记忆优化器

# 用户工作目录结构（运行时创建）
workspace/
├── MEMORY.md               # 长期记忆（精选状态）
├── memory/
│   └── YYYY-MM-DD.md       # 每日交互日志
└── backup/
    └── memory_backup_*.md  # 优化前备份
```

#### 实施步骤

**步骤 1: 实现 LongTermMemory** (`long_term_memory.py`)

核心功能：
- `init_memory_file(working_dir)`: 首次使用时创建 MEMORY.md
- `load_memory()`: 读取 MEMORY.md 内容
- `save_memory(content)`: 覆写 MEMORY.md（状态覆盖，非追加）
- `append_daily_log(date, content)`: 追加到当日日志
- `get_daily_log(date)`: 读取指定日期日志
- `list_log_dates()`: 返回所有有日志的日期列表

MEMORY.md 结构模板：
```markdown
# 长期记忆

## 用户画像
- 姓名：
- 健身目标：
- 偏好训练类型：
- 饮食偏好：

## 关键信息
- 重要日期（开始日期、里程碑等）：
- 历史最佳记录：
- 特殊注意事项（伤病、禁忌等）：

## 交互总结
- 最近关注的话题：
- 待解决的问题：
- 用户反馈和调整：
```

每日日志结构 (`memory/YYYY-MM-DD.md`):
```markdown
# 日志 2026-05-04

## 主要交互
- [时间] 用户询问：...
- [时间] Agent 建议：...

## 关键决策
- 用户决定：...

## 用户反馈
- 喜欢/不喜欢的方面：...
```

**步骤 2: 集成到 Agent 创建流程** (`agent.py`)

修改 `create_user_agent()`:
1. 初始化 LongTermMemory 实例
2. 确保 MEMORY.md 存在（从模板创建或使用默认内容）
3. 将 MEMORY.md 内容注入到 system prompt 的 "记忆" 部分
4. 注册记忆工具（memory_read, memory_write, memory_update）

**步骤 3: 添加记忆工具** (`harness/tools/memory_tools.py`)

新增工具：
- `memory_read(query: str)`: 读取长期记忆中相关内容
- `memory_write(content: str, category: str)`: 写入新记忆
- `memory_update(category: str, content: str)`: 更新指定类别记忆
- `memory_list_categories()`: 列出所有记忆类别

这些工具注册到 Toolkit，供 Agent 在对话中使用。

**步骤 4: 实现 MemoryOptimizer** (`memory_optimizer.py`)

Dream 优化流程：
- `optimize(working_dir, date)`: 对指定日期进行优化
  1. 读取当日日志 + 现有 MEMORY.md
  2. 调用 LLM 生成优化后的记忆（去重、合并、提炼）
  3. 备份现有 MEMORY.md 到 backup/
  4. 覆写 MEMORY.md 为优化后的内容
  5. 归档当日日志（标记为已优化）

优化触发时机：
- 手动触发（通过 API）
- 会话结束时自动触发
- 空闲时后台任务触发

**步骤 5: 添加 API 路由** (`app/routers/memory.py`)

端点设计：
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/agent/memory` | 获取当前长期记忆内容 |
| PUT | `/api/agent/memory` | 更新长期记忆 |
| GET | `/api/agent/memory/logs` | 列出所有日志日期 |
| GET | `/api/agent/memory/logs/{date}` | 获取指定日期日志 |
| POST | `/api/agent/memory/optimize` | 触发记忆优化 |
| DELETE | `/api/agent/memory/logs/{date}` | 删除指定日志 |

### 2.2 前端实现

#### 文件结构
```
console/src/
├── pages/
│   └── MemoryManager/
│       ├── index.tsx           # 主页面
│       └── components/
│           ├── MemoryEditor.tsx    # 记忆编辑器
│           ├── DailyLogList.tsx    # 日志列表
│           └── LogViewer.tsx       # 日志查看器
├── services/
│   └── memory.ts               # Memory API 服务
```

#### 页面设计

**MemoryManager 页面** (`/memory` 路由)

布局结构（双栏布局）：
- 左侧（60%）：长期记忆编辑器
  - MEMORY.md 内容（Markdown 编辑器，支持实时预览）
  - 保存按钮
  - "优化记忆" 按钮（触发 Dream 优化）
- 右侧（40%）：日志历史
  - 日期选择器（按日期筛选）
  - 日志列表（可展开查看）
  - 删除日志按钮

**MemoryEditor 组件**:
```
┌───────────────────────────────────────┐
│ 长期记忆                        [保存] │
│ ┌───────────────────────────────────┐ │
│ │ # 长期记忆                        │ │
│ │ ## 用户画像                       │ │
│ │ - 健身目标：增肌                  │ │
│ │ - 偏好：力量训练                  │ │
│ │                                   │ │
│ │ ## 关键信息                       │ │
│ │ ...                               │ │
│ └───────────────────────────────────┘ │
│ [优化记忆] [重置]                     │
└───────────────────────────────────────┘
```

**DailyLogList 组件**:
```
┌────────────────────────┐
│ 日志历史                │
│ ┌────────────────────┐ │
│ │ 📅 2026-05-04  ▼  │ │
│ │   - 用户询问训练计划│ │
│ │   - 完成胸部训练    │ │
│ └────────────────────┘ │
│ ┌────────────────────┐ │
│ │ 📅 2026-05-03  ▼  │ │
│ │   - 记录饮食        │ │
│ └────────────────────┘ │
└────────────────────────┘
```

**API 服务** (`services/memory.ts`):
```typescript
export interface MemoryContent {
  content: string;
  last_updated: string;
}

export interface DailyLog {
  date: string;
  content: string;
}

export const memoryApi = {
  get: (): Promise<MemoryContent> => api.get('/agent/memory'),
  update: (content: string) => api.put('/agent/memory', { content }),
  listLogs: (): Promise<string[]> => api.get('/agent/memory/logs'),
  getLog: (date: string) => api.get(`/agent/memory/logs/${date}`),
  optimize: () => api.post('/agent/memory/optimize'),
  deleteLog: (date: string) => api.delete(`/agent/memory/logs/${date}`),
};
```

---

## 第三部分：上下文生命周期管理

### 3.1 后端实现

#### 文件结构
```
rogers/src/agents/harness/context/
├── lifecycle_hooks.py      # 四阶段钩子管理器
└── tool_result_cache.py    # 工具结果文件缓存
```

#### 实施步骤

**步骤 1: 实现四阶段钩子系统** (`lifecycle_hooks.py`)

定义统一的钩子接口：
```python
class LifecycleHook(Protocol):
    async def pre_reply(self, agent, kwargs) -> dict | None: ...
    async def pre_reasoning(self, agent, kwargs) -> dict | None: ...
    async def post_acting(self, agent, kwargs, output) -> Msg | None: ...
    async def post_reply(self, agent, kwargs, output) -> Msg | None: ...
```

实现四个钩子处理器：

**pre_reply** (新增):
- 检查最终回复是否包含未处理的工具调用
- 验证回复格式和长度
- 记录遥测数据

**pre_reasoning** (现有，需重构):
- 将现有 `memory_compaction.py` 的逻辑重构为钩子
- 保留上下文压缩功能
- 添加上下文健康检查日志

**post_acting** (现有 `compact_tool_result` 增强):
- 工具执行后检查结果大小
- 超大结果保存到文件缓存
- 上下文中替换为文件引用
- 保留最近的 N 条完整结果

**post_reply** (新增):
- 保存会话状态
- 触发每日日志写入
- 记录 token 使用统计
- 清理临时文件

**步骤 2: 实现工具结果文件缓存** (`tool_result_cache.py`)

功能：
- `cache_result(session_id, tool_name, content)`: 保存大结果到文件
- `get_cached_result(cache_id)`: 读取缓存结果
- `cleanup_expired(retention_days)`: 清理过期缓存
- 文件路径：`workspace/tool_results_cache/{session_id}/{timestamp}_{tool_name}.txt`

配置项 (添加到 `ToolResultCompactConfig`):
- `cache_enabled: bool` - 是否启用文件缓存
- `cache_max_bytes: int` - 超过此大小则缓存到文件（默认 10000）
- `retention_days: int` - 缓存保留天数（默认 7）

**步骤 3: 集成到 Agent** (`agent.py`)

修改 Agent 创建流程：
1. 实例化 `LifecycleHooksManager`
2. 注册四个钩子到 AgentScope 的钩子系统
3. 初始化工具结果缓存

钩子注册示例：
```python
lifecycle = LifecycleHooksManager(
    memory_manager=reme_memory,
    context_config=config.context_compact,
    cache_config=config.tool_result_compact,
)

agent.register_hook("pre_reply", lifecycle.pre_reply)
agent.register_hook("pre_reasoning", lifecycle.pre_reasoning)
agent.register_hook("post_acting", lifecycle.post_acting)
agent.register_hook("post_reply", lifecycle.post_reply)
```

**步骤 4: 添加 API 路由** (`app/routers/context.py`)

端点设计：
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/agent/context/stats` | 获取上下文统计信息 |
| GET | `/api/agent/context/cache` | 列出工具结果缓存 |
| GET | `/api/agent/context/cache/{id}` | 获取缓存内容 |
| DELETE | `/api/agent/context/cache` | 清理所有缓存 |
| POST | `/api/agent/context/compact` | 手动触发上下文压缩 |

**步骤 5: 扩展配置系统** (`config.py`)

在 `ContextCompactConfig` 中添加：
- `lifecycle_hooks_enabled: bool` - 是否启用四阶段钩子
- `telemetry_enabled: bool` - 是否记录钩子调用日志

在 `ToolResultCompactConfig` 中添加：
- `file_cache_enabled: bool` - 是否启用文件缓存
- `file_cache_max_bytes: int` - 缓存阈值
- `file_cache_retention_days: int` - 保留天数

### 3.2 前端实现

#### 文件结构
```
console/src/
├── pages/
│   └── ContextManager/
│       ├── index.tsx           # 主页面
│       └── components/
│           ├── ContextStats.tsx    # 上下文统计卡片
│           ├── CacheList.tsx       # 缓存列表
│           └── CompactTrigger.tsx  # 压缩触发器
├── services/
│   └── context.ts              # Context API 服务
```

#### 页面设计

**ContextManager 页面** (`/context` 路由)

布局结构：
- 顶部：上下文统计卡片（4 个指标卡片）
  - 当前 Token 使用量 / 总限制
  - 压缩次数（今日/总计）
  - 缓存文件数 / 总大小
  - 平均响应 Token 数
- 中部：工具结果缓存列表
  - 表格显示：工具名、大小、时间、操作
  - 分页、搜索、按日期筛选
  - 批量清理按钮
- 底部：手动操作区
  - "压缩上下文" 按钮
  - "清理缓存" 按钮

**ContextStats 组件**:
```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Tokens  │ │ 压缩次数 │ │ 缓存    │ │ 平均响应│
│ 45,230  │ │ 12      │ │ 23/15MB │ │ 1,250   │
│ / 131K  │ │ 今日/总计│ │ 文件/大小│ │ tokens  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
```

**CacheList 组件**:
```
┌──────────────────────────────────────────────┐
│ 工具结果缓存                [清理全部]        │
│ ┌────┬──────────┬──────┬──────────┬────────┐ │
│ │ ✓  │ 工具名称  │ 大小  │ 时间      │ 操作   │ │
│ ├────┼──────────┼──────┼──────────┼────────┤ │
│ │ ☐  │ read_file│ 25KB  │ 10:30 AM │ [查看] │ │
│ │ ☐  │ search   │ 12KB  │ 09:15 AM │ [查看] │ │
│ └────┴──────────┴──────┴──────────┴────────┘ │
└──────────────────────────────────────────────┘
```

**API 服务** (`services/context.ts`):
```typescript
export interface ContextStats {
  current_tokens: number;
  max_tokens: number;
  compaction_count_today: number;
  compaction_count_total: number;
  cache_file_count: number;
  cache_total_size_bytes: number;
  avg_response_tokens: number;
}

export interface CacheEntry {
  id: string;
  tool_name: string;
  size_bytes: number;
  created_at: string;
}

export const contextApi = {
  getStats: (): Promise<ContextStats> => api.get('/agent/context/stats'),
  listCache: (): Promise<CacheEntry[]> => api.get('/agent/context/cache'),
  getCache: (id: string) => api.get(`/agent/context/cache/${id}`),
  clearCache: () => api.delete('/agent/context/cache'),
  triggerCompact: () => api.post('/agent/context/compact'),
};
```

---

## 第四部分：路由和导航集成

### 4.1 后端路由注册

在 `app/main.py` 中注册新路由：
```python
from app.routers import skills, memory, context

app.include_router(skills.router)
app.include_router(memory.router)
app.include_router(context.router)
```

### 4.2 前端路由添加

在 `console/src/App.tsx` 中添加路由：
```typescript
import { SkillManager, MemoryManager, ContextManager } from './pages';

// 在 MainLayout 内添加路由
<Route path="/skills" element={<SkillManager />} />
<Route path="/memory" element={<MemoryManager />} />
<Route path="/context" element={<ContextManager />} />
```

### 4.3 侧边栏导航更新

在 `console/src/components/MainLayout/index.tsx` 的 Sider 中添加菜单项：
- 技能管理 (Tool 图标)
- 记忆管理 (Book 图标)
- 上下文管理 (Dashboard 图标)

---

## 实施顺序和依赖关系

```
阶段 1 (第 1 步):
├─ Skill 数据模型
├─ SkillManager 基础
└─ Skill 扫描和加载

阶段 2 (第 2 步):
├─ Skill API 路由
├─ Skill 前端页面
└─ 侧边栏集成

阶段 3 (第 3 步):
├─ LongTermMemory 基础
├─ MEMORY.md 模板
└─ 每日日志系统

阶段 4 (第 4 步):
├─ 记忆 API 路由
├─ 记忆前端页面
└─ 记忆工具注册

阶段 5 (第 5 步):
├─ 四阶段钩子接口
├─ 重构 pre_reasoning 钩子
├─ 实现 post_acting 增强
└─ 工具结果文件缓存

阶段 6 (第 6 步):
├─ 上下文 API 路由
├─ 上下文前端页面
└─ 配置系统扩展
```

---

## 关键技术注意事项

### 5.1 向后兼容
- 现有工具和功能不受影响
- Skill 系统默认不启用任何技能（空目录）
- 长期记忆系统自动初始化，不干扰现有 ReMeLight 记忆
- 四阶段钩子默认启用，但可通过配置关闭

### 5.2 性能考虑
- Skill 扫描在 Agent 初始化时执行一次，后续使用缓存
- MEMORY.md 文件大小限制（建议 10KB 以内）
- 工具结果缓存自动清理，避免磁盘占用无限增长
- Dream 优化在空闲时执行，不影响正常响应

### 5.3 安全考虑
- Skill 上传入前校验：文件大小、文件类型、路径遍历检查
- MEMORY.md 写入前校验：内容长度、特殊字符过滤
- 工具结果缓存文件名使用安全字符（去除路径分隔符）
- 所有 API 端点需要认证（JWT token）

### 5.4 Windows 兼容性
- 文件路径使用 `pathlib` 处理跨平台差异
- 文件名避免 Windows 非法字符（\ / : * ? " < > |）
- 文件锁机制防止并发写入冲突

---

## 预期效果

### Skill 系统
- 用户可以自行扩展 Agent 能力，不局限于预定义的 22 个工具
- 技能包可以分享和复用
- Agent 能力配置更加灵活

### 长期记忆
- Agent 记住用户偏好和历史决策，不再仅限于会话内记忆
- 每日日志提供交互审计追踪
- Dream 优化保持记忆质量，避免信息膨胀

### 上下文生命周期
- 更精细的上下文控制，减少信息丢失
- 工具结果缓存提升大会话性能
- 四阶段钩子提供完整的生命周期可见性
