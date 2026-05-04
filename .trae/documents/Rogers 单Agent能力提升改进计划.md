# Rogers 单 Agent 能力改进计划 - 向 QwenPaw 学习

## 一、现状对比分析

### 1.1 架构对比

| 维度         | Rogers (当前)           | QwenPaw (目标)                                                 |
| ---------- | --------------------- | ------------------------------------------------------------ |
| **核心框架**   | AgentScope ReActAgent | AgentScope ReActAgent (相同)                                   |
| **工具数量**   | \~22个 (12读+9写+1多模态)   | 20+内置+MCP动态+Skill扩展+ACP外部                                    |
| **记忆系统**   | ReMeLight (向量+FTS)    | ReMeLight + MEMORY.md长期记忆+每日日志+Dream优化                       |
| **上下文管理**  | pre\_reasoning钩子压缩    | 4个生命周期钩子(pre\_reply/pre\_reasoning/post\_acting/post\_reply) |
| **扩展机制**   | 固定工具集                 | Skill系统(双层架构+6+平台Hub)                                        |
| **权限控制**   | 无                     | Tool Guard分级审批                                               |
| **外部集成**   | 无                     | MCP协议+ACP外部Agent委派                                           |
| **多Agent** | 无                     | MultiAgentManager(懒加载/热重载)                                   |
| **通信渠道**   | HTTP API + SSE        | 12+渠道(Discord/Telegram/钉钉/飞书/微信等)                            |
| **主动交互**   | 无                     | Proactive主动交互+Heartbeat定时任务                                  |
| **安全特性**   | 基础路径隔离                | Tool Guard+Skill扫描+路径检查+ZIP安全                                |

### 1.2 能力差距矩阵

| 能力域       | Rogers          | QwenPaw                | 差距等级 |
| --------- | --------------- | ---------------------- | ---- |
| 工具系统扩展性   | 固定注册            | Skill动态加载              | 🔴 高 |
| 记忆长期维护    | 对话压缩+搜索         | MEMORY.md状态化记忆+Dream优化 | 🟡 中 |
| 危险操作审批    | 无               | Tool Guard两级审批         | 🟡 中 |
| MCP协议集成   | 无               | HTTP+StdIO双模式          | 🟡 中 |
| 上下文生命周期   | 仅pre\_reasoning | 4阶段钩子                  | 🟢 低 |
| 外部Agent委派 | 无               | ACP协议                  | 🟢 低 |
| 定时任务      | 无               | Heartbeat+Cron         | 🟢 低 |
| 主动交互      | 无               | Proactive空闲检测          | 🟢 低 |
| 多Agent协作  | 无               | MultiAgentManager      | ⚪ 可选 |

***

## 二、改进路线图

### 阶段一：核心扩展能力 (高优先级)

#### 1. Skill 技能系统

**目标：** 引入可插拔的 Skill 机制，使 Rogers 能够动态扩展能力

**具体步骤：**

1.1 **定义 Skill 格式规范**

* 创建 `SKILL.md` 格式标准（YAML frontmatter + Markdown body）

* 定义必要字段：name, version, description, triggers, channels

* 定义可选字段：config\_schema, dependencies, tags

1.2 **实现 Skill 加载器**

* 扫描工作目录下的 `skills/` 文件夹

* 解析 SKILL.md 并注册为可调用工具

* 支持中英文双语版本

* 实现 Skill 版本管理和更新检测

1.3 **构建 Skill 工具注册**

* 将 Skill 描述的 capability 自动注册为 Agent 可用工具

* 支持工具级别的启用/禁用

* 支持按用户配置覆盖

1.4 **实现 Skill Hub 客户端（可选）**

* 支持从在线 Hub 搜索和安装技能

* 支持技能包导入/导出

* 技能安全扫描机制

#### 2. 工具权限控制 (Tool Guard)

**目标：** 引入分级权限控制，防止危险操作误执行

**具体步骤：**

2.1 **定义危险工具清单**

* 识别 Rogers 中的危险操作（如删除训练计划、更新健康数据等）

* 按风险等级分类：READ（安全）、WRITE（通知）、DELETE（审批）

2.2 **实现 Tool Guard Mixin**

* 工具执行前拦截检查

* 支持两种模式：

  * `approve`: 首次使用需用户审批，通过后缓存权限

  * `notify`: 仅通知用户，自动执行

2.3 **集成 SSE 审批事件**

* 扩展 `/api/agent` SSE 流，新增 `approval_request` 事件类型

* 实现审批状态缓存和管理

* 前端需要配合展示审批弹窗

#### 3. MCP (Model Context Protocol) 集成

**目标：** 支持动态接入外部 MCP 服务器提供的工具

**具体步骤：**

3.1 **实现 MCP 客户端管理器**

* 支持 HTTP 和 StdIO 两种传输模式

* 实现 MCP 工具发现和注册

* 工具名称空间隔离（避免与内置工具冲突）

3.2 **配置系统扩展**

* 在 `agent.json` 中增加 `mcp_servers` 配置项

* 支持每个 MCP 服务器的独立启停

* 支持环境变量注入

3.3 **热重载机制**

* MCP 配置变更时动态替换连接，不重启 Agent

* 连接状态监控和自动重连

***

### 阶段二：记忆和上下文增强 (中优先级)

#### 4. 长期记忆系统升级

**目标：** 从单纯的对话压缩升级为状态化长期记忆

**具体步骤：**

4.1 **引入 MEMORY.md 机制**

* 在工作目录创建 `MEMORY.md` 文件作为长期记忆存储

* 定义记忆结构：用户偏好、重要日期、关键目标、历史总结

* 记忆状态覆盖而非追加（避免无限增长）

4.2 **每日日志系统**

* 每次会话结束自动生成当日日志（`memory/YYYY-MM-DD.md`）

* 记录关键交互、决策、用户反馈

* 支持按日期范围检索

4.3 **Dream 记忆优化**

* 创建独立的 DreamOptimizer Agent

* 定期（会话结束时或空闲时）运行优化：

  * 读取当日日志和现有 MEMORY.md

  * 去重、合并、提炼高价值信息

  * 优化前自动备份

* 支持中英文双语优化

4.4 **记忆文件监控器**

* 监控工作目录文件变更

* 自动索引新内容到向量数据库

* 提升记忆搜索的实时性

#### 5. 上下文生命周期管理增强

**目标：** 从单一的 pre\_reasoning 钩子扩展为完整的生命周期管理

**具体步骤：**

5.1 **实现四阶段钩子系统**

* `pre_reply`: Agent 回复前最终检查

* `pre_reasoning`: 每轮推理前上下文健康检查+压缩（已有）

* `post_acting`: 工具执行后结果裁剪（已有，需增强）

* `post_reply`: 最终回复后日志/遥测

5.2 **工具结果文件缓存**

* 超大工具输出保存到 `tool_results_cache/` 目录

* 上下文中替换为文件引用

* 可配置保留天数（当前已在 compact\_tool\_result 中部分实现）

5.3 **Token 感知增强**

* 更精确的 token 估算（考虑不同模型的差异）

* 动态阈值调整（根据当前模型的最大上下文）

***

### 阶段三：高级特性 (低优先级/可选)

#### 6. 定时任务和 Heartbeat

**目标：** 支持定时自动执行 Agent 任务

**具体步骤：**

6.1 **实现 Cron 任务管理器**

* 支持间隔模式（`30m`, `1h`, `2h30m`）

* 支持标准 Cron 表达式

* 任务状态追踪和错误重试

6.2 **实现 Heartbeat 机制**

* 读取 `HEARTBEAT.md` 作为定时查询内容

* 活跃时间窗口控制（避免深夜打扰）

* 结果自动推送到最后使用的渠道

#### 7. 主动交互 (Proactive)

**目标：** Agent 在空闲时主动提供帮助和建议

**具体步骤：**

7.1 **空闲检测**

* 可配置空闲时间阈值

* 基于最后一条消息时间计算

7.2 **任务提取**

* 从历史会话中提取潜在未完成需求

* 识别用户可能的下一步意图

7.3 **智能触发**

* 基于会话上下文生成主动消息

* 避免频繁打扰（可配置最大频率）

#### 8. 会话状态持久化增强

**目标：** 提升会话管理的可靠性和跨平台兼容性

**具体步骤：**

8.1 **JSONL 消息存储**

* 将消息按日期分组存储为 `YYYY-MM-DD.jsonl`

* 提升大会话的读写性能

8.2 **JSON 损坏恢复**

* 实现 `raw_decode` 提取第一个有效 JSON 对象

* 防止意外中断导致的数据丢失

8.3 **异步文件 I/O**

* 使用 `aiofiles` 避免阻塞事件循环

#### 9. ACP 外部 Agent 协议（可选）

**目标：** 支持将复杂任务委派给外部专用 Agent

**具体步骤：**

9.1 **定义 ACP 通信协议**

* 支持 opencode、qwen\_code、claude\_code、codex 等

* 流式事件转发

* 状态快照同步

9.2 **实现委派工具**

* `delegate_external_agent` 工具

* 任务进度查询和结果获取

***

## 三、实施优先级建议

### 立即实施（1-2周）

1. **Skill 技能系统基础** - 为后续扩展打下基础
2. **Tool Guard 权限控制** - 提升系统安全性

### 短期规划（2-4周）

1. **MCP 集成** - 扩展工具生态
2. **长期记忆升级 (MEMORY.md)** - 提升记忆质量
3. **上下文四阶段钩子** - 优化上下文管理

### 中期规划（1-2月）

1. **Dream 记忆优化** - 自动维护记忆质量
2. **定时任务/Heartbeat** - 自动化能力
3. **会话持久化增强** - 提升可靠性

### 长期规划（按需）

1. **Proactive 主动交互** - 提升用户体验
2. **ACP 外部 Agent 协议** - 任务委派能力
3. **多 Agent 协作** - 架构升级

***

## 四、技术风险与注意事项

### 4.1 兼容性风险

* Skill 系统需要保证向后兼容，现有工具不应受影响

* MCP 集成需要考虑不同服务器的协议版本差异

* Dream 优化需要使用与主 Agent 相同的模型配置

### 4.2 性能风险

* Skill 加载器需要在启动时预热，避免首次调用延迟

* 记忆文件监控器需要防抖机制，避免频繁 I/O

* Dream 优化应在 Agent 空闲时运行，避免影响正常响应

### 4.3 安全风险

* Skill 安装前必须进行安全扫描

* 危险工具审批需要严格的权限验证

* MCP 工具名称空间隔离防止冲突

### 4.4 用户体验

* 权限审批流程需要简洁，避免过多弹窗

* Skill 管理需要提供清晰的 UI 界面

* 记忆优化过程需要透明，用户可查看优化日志

***

## 五、预期收益

### 5.1 能力提升

* **工具扩展性**：从固定 22 个工具提升到无限 Skill 扩展

* **记忆质量**：从对话压缩升级为智能长期记忆

* **安全性**：危险操作可控，用户信任度提升

* **自动化**：定时任务和主动交互减少用户操作负担

### 5.2 架构优势

* **可插拔**：Skill 系统使功能模块化

* **可组合**：MCP 协议允许跨系统工具集成

* **可维护**：四阶段钩子使生命周期管理清晰

* **可扩展**：为未来多 Agent 协作打下基础

### 5.3 用户体验

* **智能**：记忆优化和主动交互使 Agent 更贴心

* **安全**：权限控制让用户放心使用

* **灵活**：Skill Hub 允许用户按需安装功能

***

## 六、关键文件参考

### Rogers 当前核心文件

| 文件                                                     | 作用          |
| ------------------------------------------------------ | ----------- |
| `rogers/src/agents/agent.py`                           | Agent 工厂和缓存 |
| `rogers/src/agents/config.py`                          | 配置体系        |
| `rogers/src/agents/harness/tools/`                     | 工具函数        |
| `rogers/src/agents/harness/memory/reme_light.py`       | 记忆管理        |
| `rogers/src/agents/harness/hooks/memory_compaction.py` | 上下文压缩       |
| `rogers/src/agents/harness/context.py`                 | 请求级上下文隔离    |
| `rogers/src/agents/harness/sessions/user_session.py`   | 会话管理        |

### QwenPaw 参考实现

| 文件                                                       | 可借鉴功能         |
| -------------------------------------------------------- | ------------- |
| `src/qwenpaw/agents/skills_manager.py`                   | Skill 生命周期管理  |
| `src/qwenpaw/agents/tool_guard_mixin.py`                 | 危险操作权限拦截      |
| `src/qwenpaw/agents/memory/base_memory_manager.py`       | 记忆管理抽象基类      |
| `src/qwenpaw/agents/memory/reme_light_memory_manager.py` | Dream 记忆优化    |
| `src/qwenpaw/agents/context/base_context_manager.py`     | 四阶段钩子         |
| `src/qwenpaw/app/mcp/manager.py`                         | MCP 客户端管理     |
| `src/qwenpaw/app/crons/heartbeat.py`                     | 定时任务          |
| `src/qwenpaw/agents/skills_hub.py`                       | Skill Hub 客户端 |

