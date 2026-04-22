# Phase 02 开发计划：评估中心基础能力（Assessment Foundation）

## 1. 阶段目标

- 在已完成认证模块基础上，落地“评估中心”最小可用闭环：
  - 新建评估
  - 查询评估详情
  - 完成评估并生成基础报告
- 打通前后端第一条业务数据链路，为体成分/体态/动作筛查模块接入做准备。

## 2. 范围（In Scope）

### 2.1 后端 API 与功能

- `POST /api/v1/assessments`
  - 创建评估记录（关联当前用户、评估目标、风险问卷摘要）。
- `GET /api/v1/assessments/{id}`
  - 获取评估详情（基础信息 + 当前状态）。
- `POST /api/v1/assessments/{id}/complete`
  - 完成评估并冻结关键结果。
- `GET /api/v1/assessments/{id}/report`
  - 返回基础报告（分层风险标签、关键建议摘要）。

### 2.2 前端页面与功能

- 新增页面：`/assessment-center`
- 支持功能：
  - 评估列表（按状态筛选：进行中/已完成）
  - 新建评估表单
  - 评估详情抽屉或详情页
  - 完成评估操作与结果展示

## 3. 不在本阶段（Out of Scope）

- 复杂评分引擎（仅接入基础规则版本）。
- 设备自动采集（先走手动录入/模拟数据）。
- 多角色复杂权限矩阵（本阶段仅保留最小可用鉴权边界）。

## 4. 后端设计

### 4.1 数据模型（建议）

- `assessments`
  - `id`, `member_id`, `status`, `goal`, `risk_level`,
  - `questionnaire_summary`, `report_summary`,
  - `created_at`, `updated_at`, `completed_at`
- `status` 枚举建议：`draft`, `in_progress`, `completed`
- `risk_level` 枚举建议：`low`, `medium`, `high`

### 4.2 分层落位

- API：`Rogers/app/api/v1/assessments.py`
- Schemas：`Rogers/app/schemas/assessment.py`
- Services：`Rogers/app/services/assessment_service.py`
- Repositories：`Rogers/app/repositories/assessment_repository.py`
- Models：`Rogers/app/models/assessment.py`

### 4.3 核心业务规则

- 登录用户可为自己创建评估。
- `completed` 状态不可再次编辑核心字段。
- 报告读取必须校验当前用户权限（仅允许评估所属用户读取）。

## 5. 前端设计

### 5.1 路由与结构

- 页面：`webpage/src/pages/assessment-center/`
- Feature：`webpage/src/features/assessment/`
- API：`webpage/src/shared/api/assessment.ts`

### 5.2 UI 交互

- 主体采用深色卡片布局，符合现有主题。
- 列表页首屏展示关键字段：会员、评估日期、状态、风险等级。
- 新建评估采用分区表单：基础信息 -> 问卷摘要 -> 确认提交。
- 完成评估后弹出报告摘要卡，并可跳转报告详情。

## 6. 任务拆解

### 6.1 后端任务

1. 新增 assessment 模型与迁移。
2. 完成 repository/service/api 三层实现。
3. 增加权限校验与状态流转控制。
4. 补充集成测试：创建、查询、完成、报告。

### 6.2 前端任务

1. 实现评估中心页面框架与路由接入。
2. 封装 assessment API 与类型定义。
3. 完成新建评估表单与列表展示。
4. 实现完成评估动作与报告摘要展示。

## 7. 验收标准（Definition of Done）

- 登录后可进入评估中心并创建评估。
- 可查看评估详情并将评估置为完成状态。
- 可读取基础评估报告（含风险标签与建议摘要）。
- 核心接口具备成功/失败/权限失败测试覆盖。
- 前后端字段命名一致，文档与实现一致。

## 8. 风险与注意事项

- 若先使用 SQLite，需提前规避 PostgreSQL 语法差异。
- 状态流转必须在服务层做统一校验，避免多入口绕过规则。
- 接口响应建议逐步向统一格式（`code/message/data/request_id`）收敛。
