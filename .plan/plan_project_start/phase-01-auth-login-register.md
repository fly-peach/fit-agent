# Phase 01 开发计划：用户登录与注册

## 1. 目标与范围

### 1.1 目标
- 完成系统首个可交付闭环：用户注册 -> 登录 -> 获取当前用户信息。
- 为后续评估、训练、分析模块提供统一认证基线（JWT）。

### 1.2 范围（In Scope）
- 后端认证 API：注册、登录、刷新令牌、获取当前用户。
- 前端认证页面：登录页、注册页、基础受保护路由。
- 认证状态管理：Token 存储、自动注入请求头、过期处理。

### 1.3 暂不包含（Out of Scope）
- 第三方登录（微信/钉钉/短信）。
- 找回密码、邮箱验证、双因子认证。
- 复杂权限系统（仅保留最小可用鉴权基线）。

## 2. 后端 API 设计与功能

### 2.1 模块结构（符合分层）
- API：`rogers/app/api/v1/auth.py`
- Schemas：`rogers/app/schemas/auth.py`、`rogers/app/schemas/user.py`
- Services：`rogers/app/services/auth_service.py`
- Repositories：`rogers/app/repositories/user_repository.py`
- Models：`rogers/app/models/user.py`
- Core：`rogers/app/core/security.py`、`rogers/app/core/config.py`

### 2.2 数据模型（User）
- 字段：`id`、`email`（唯一）、`phone`（可空唯一）、`password_hash`、`name`、`is_active`、`created_at`、`updated_at`。
- 索引：`email` 唯一索引；`phone` 唯一索引（允许空）。

### 2.3 API 列表（v1）
- `POST /api/v1/auth/register`
  - 功能：创建用户并返回用户基础信息（不返回明文密码）。
  - 请求：`email | phone` 至少一个 + `password` + `name`（可选，默认值由服务端补齐）。
  - 响应：`user` + `access_token` + `refresh_token`（可配置为注册后自动登录）。
- `POST /api/v1/auth/login`
  - 功能：账号密码登录，签发 token。
  - 请求：`account`（邮箱或手机号）+ `password`。
  - 响应：`access_token`、`refresh_token`、`token_type`、`expires_in`。
- `POST /api/v1/auth/refresh`
  - 功能：用 refresh token 换取新 access token。
- `GET /api/v1/auth/me`
  - 功能：返回当前登录用户信息，用于前端启动鉴权。

### 2.4 安全策略
- 密码哈希：`passlib[bcrypt]`。
- Token：JWT（`access_token` 短时 + `refresh_token` 长时）。
- 过期策略：access 30 分钟，refresh 7-14 天（配置化）。
- 基础防护：登录失败统一错误提示、最小密码强度校验、禁用用户拒绝登录。

### 2.5 错误码与响应约定
- `400`：参数错误/格式非法。
- `401`：认证失败（账号或密码错误、token 无效）。
- `403`：用户被禁用。
- `409`：邮箱或手机号已存在。
- 响应体统一：`code`、`message`、`data`、`request_id`（后续接入日志链路）。

### 2.6 交付清单
- Alembic 初始迁移：新增 `users` 表。
- 认证依赖：`get_current_user()`、`get_current_active_user()`。
- OpenAPI 文档可见并可调试四个认证接口。
- 单元测试与集成测试覆盖核心路径。

## 3. 前端对应实现

### 3.1 页面与路由
- 页面：`/login`、`/register`。
- 受保护路由：`/dashboard`（未登录自动跳转 `/login`）。
- 登录后跳转：默认进入 `/dashboard`，支持携带 `redirect` 参数。

### 3.2 功能点
- 登录表单：账号（邮箱/手机号）+ 密码，支持显示/隐藏密码。
- 注册表单：姓名（可选）、邮箱/手机号、密码、确认密码。
- 表单校验：必填、邮箱格式、手机号格式、密码长度与复杂度、二次密码一致。
- 状态反馈：提交中态、接口错误提示、成功提示。

### 3.3 前端技术落点
- API：`webpage/src/shared/api/auth.ts`
- Feature：`webpage/src/features/auth/*`
- Pages：`webpage/src/pages/auth/login`、`webpage/src/pages/auth/register`
- Store：`webpage/src/store/auth.ts`（或 `zustand` 同等实现）
- Route Guard：`webpage/src/router/guards.tsx`

### 3.4 Token 与会话管理
- 存储策略：`access_token` 内存优先 + `refresh_token` 安全持久化（初版可 localStorage，后续切 HttpOnly Cookie）。
- 请求拦截：自动附加 `Authorization: Bearer <token>`。
- 失效处理：`401` 自动尝试 refresh，失败则清理会话并跳转登录页。

## 4. 开发任务拆解

### 4.1 后端任务
1. 建立用户模型与迁移脚本。
2. 实现密码哈希与 JWT 工具函数。
3. 完成 auth repository/service/api 三层实现。
4. 编写依赖注入与鉴权中间层。
5. 增加单元测试、集成测试。

### 4.2 前端任务
1. 实现登录/注册页面及交互。
2. 封装认证 API 与数据类型。
3. 建立认证状态 store 与拦截器。
4. 实现路由守卫与重定向逻辑。
5. 联调并完善异常提示。

## 5. 验收标准（Definition of Done）
- 可成功注册新用户并立即登录。
- 已注册用户可登录并访问受保护页面。
- Token 过期后可自动刷新；刷新失败会强制重新登录。
- 接口错误在前端可读且可定位。
- 核心认证流程测试通过，且文档与实现一致。
