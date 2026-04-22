# Phase 03 开发计划：体成分接入 MVP（Body Composition Intake & Trend）

## 1. 阶段目标

- 在已完成认证（Phase 01）与评估中心基础能力（Phase 02）的基础上，落地体成分数据的最小可用闭环：
  - 体成分记录录入（手动/模拟）
  - 体成分记录列表与详情查询
  - 单指标趋势序列（用于折线图）
  - 两次记录对比（变化值/变化率）
- 将体成分关键指标纳入评估报告输出（增强 Phase 02 的报告可读性），形成“评估中心 + 体成分”可演示链路。

## 2. 范围（In Scope）

### 2.1 后端 API 与功能

- `POST /api/v1/body-composition`
  - 创建一条体成分记录（关联当前用户；可选关联 assessment）。
- `GET /api/v1/body-composition`
  - 查询体成分记录列表（按时间区间分页；可选按 assessment 过滤）。
- `GET /api/v1/body-composition/{id}`
  - 查询体成分记录详情。
- `GET /api/v1/body-composition/trend`
  - 按 metric + 时间区间返回趋势序列（用于折线图）。
- `GET /api/v1/body-composition/compare`
  - 对比两条记录（差值、百分比变化、基础结论 tags）。

### 2.2 前端页面与功能

- 新增页面：`/body-composition`
  - 体成分记录列表（支持按时间区间筛选、快速跳转详情）。
- 新增页面：`/body-composition/new`
  - 体成分录入表单（基础/脂肪/肌肉/水分/代谢分组）。
- 新增页面：`/body-composition/:id`
  - 体成分详情（分组展示指标 + “与上一条对比”入口）。
- 评估中心增强（Phase 02 增量）：
  - 在评估详情/报告区域增加“体成分摘要卡”（来自最近一条记录或绑定到 assessment 的记录）。

## 3. 不在本阶段（Out of Scope）

- 设备直连/自动采集、复杂清洗与单位换算引擎。
- 体态/动作筛查采集与评分引擎。
- 综合分析大屏（analytics）与教练工作台完整功能。

## 4. 后端设计

### 4.1 数据模型（建议）

#### 4.1.1 表：`body_composition_records`

- 字段（MVP 版）
  - `id`
  - `member_id`（FK -> `users.id`）
  - `assessment_id`（可空，FK -> `assessments.id`）
  - `measured_at`（体测时间）
  - `created_at`、`updated_at`
- 指标字段（对齐体测基线字段建议，优先覆盖常用与趋势可视化指标）
  - 基础：`weight`、`bmi`
  - 脂肪：`body_fat_rate`、`visceral_fat_level`、`fat_mass`
  - 肌肉：`muscle_mass`、`skeletal_muscle_mass`、`skeletal_muscle_rate`
  - 水分：`water_rate`、`water_mass`
  - 代谢：`bmr`
- 扩展字段（用于保留原始 payload，避免字段不全导致丢信息）
  - `raw_payload`（JSON，可空）

> 字段命名与口径参考：`.plan/00-project-outline-and-metrics-baseline.md` 中的“体成分详情指标（字段建议）”。

### 4.2 分层落位

- API：`Rogers/app/api/v1/body_composition.py`
- Schemas：`Rogers/app/schemas/body_composition.py`
- Services：`Rogers/app/services/body_composition_service.py`
- Repositories：`Rogers/app/repositories/body_composition_repository.py`
- Models：`Rogers/app/models/body_composition.py`

### 4.3 核心业务规则

- 写入权限：登录用户可写入自己的体成分记录。
- 读取权限：登录用户仅可读取自己的体成分记录。
- 趋势与对比：
  - `trend` 仅返回一个 metric 的时间序列点（`measured_at` + `value`）。
  - `compare` 返回两条记录的对比对象：`a`、`b`、`diff`、`diff_ratio`、`tags`（tags 初版可规则化）。

## 5. API 设计与响应约定（v1）

### 5.1 `POST /api/v1/body-composition`

- 请求（示例）
  - `assessment_id?: int`
  - `measured_at: datetime`
  - `weight?: number`、`bmi?: number`、`body_fat_rate?: number` 等核心字段
  - `raw_payload?: object`
- 响应
  - 返回记录详情（含 `id`、`member_id`、`measured_at`、核心指标字段）

### 5.2 `GET /api/v1/body-composition`

- Query 参数
  - `from`、`to`（可选）
  - `skip`、`limit`（分页）
  - `assessment_id`（可选）
- 响应
  - 返回记录列表（按 `measured_at` 倒序）

### 5.3 `GET /api/v1/body-composition/trend`

- Query 参数
  - `metric`（必填，示例：`weight`、`body_fat_rate`）
  - `from`、`to`（可选）
- 响应
  - `[{ measured_at, value }]`

### 5.4 `GET /api/v1/body-composition/compare`

- Query 参数
  - `a`（必填，record_id）
  - `b`（必填，record_id）
- 响应
  - `a`、`b`：两条记录的核心字段快照
  - `diff`：每个可比指标的差值
  - `diff_ratio`：每个可比指标的变化率（以 a 为基准）
  - `tags`：初版规则化结论（示例：`body_fat_rate_up`、`weight_down`）

## 6. 前端设计

### 6.1 路由与目录结构

- Pages：
  - `webpage/src/pages/body-composition/`
    - `List.tsx`、`Create.tsx`、`Detail.tsx`
- Feature：
  - `webpage/src/features/body-composition/`
- API：
  - `webpage/src/shared/api/bodyComposition.ts`

### 6.2 UI 交互

- 深色卡片布局与现有主题保持一致。
- 列表页：首屏展示 `measured_at`、`weight`、`body_fat_rate`、`bmi`、`visceral_fat_level` 等关键指标。
- 详情页：按分组展示指标（基础/脂肪/肌肉/水分/代谢），并提供“与上一条对比”。
- 趋势：至少支持 `weight`、`body_fat_rate` 两个指标绘图（可先用简易折线图实现，后续再引入图表库）。
- 评估详情增强：在评估报告区域展示体成分摘要卡（来自最新记录或绑定记录）。

## 7. 任务拆解

### 7.1 后端任务

1. 新增 `body_composition_records` 模型与迁移。
2. 完成 repository/service/api 三层实现（含权限校验）。
3. 实现 trend 查询与 compare 计算（服务层统一编排）。
4. 补充集成测试：录入、列表、详情、趋势、对比、权限失败路径。

### 7.2 前端任务

1. 封装 body composition API 与类型定义。
2. 实现体成分列表页与筛选条件（时间区间）。
3. 实现录入表单（基础校验、提交中态、错误提示）。
4. 实现详情页 + 趋势图 + 对比视图。
5. 在评估详情/报告区域增加体成分摘要卡并联调。

## 8. 验收标准（Definition of Done）

- 用户登录后可录入体成分记录，并在列表与详情中查看。
- 用户仅可查看自己的体成分记录（无权查看他人）。
- 趋势接口可返回至少 `weight` 与 `body_fat_rate` 的序列数据，并在前端完成折线图展示。
- 对比接口可返回两条记录的差值与变化率，并在前端完成对比展示。
- 评估报告区域能展示体成分摘要（数据源规则在实现中与本计划一致）。
- 核心接口覆盖成功/参数失败/权限失败测试用例，字段命名与文档一致。

## 9. 风险与注意事项

- SQLite 与 PostgreSQL 对时间类型、JSON 类型支持差异需提前规避（字段与查询尽量使用通用写法）。
- 指标字段较多，MVP 需控制字段集：优先“可展示 + 可趋势 + 可对比”的字段，其余放入 `raw_payload`。
- 权限仅按当前用户过滤，避免通过参数访问他人数据。
