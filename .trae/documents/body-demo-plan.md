# 人体展示 UI - 实现计划（v2）

## 概述

在 `bodydemo/` 目录下创建一个独立的人体展示 UI，通过数据驱动来定义和可视化人体各部位的围度信息。**基于现有开源项目**，避免从零绘制 SVG 人体。

---

## GitHub 现有项目调研

### ⭐ 推荐方案：`body-muscles`（最匹配）

| 项目 | 地址 | 技术栈 | Stars | 特点 |
|------|------|--------|-------|------|
| **body-muscles** | `vulovix/body-muscles` | 纯 TypeScript, 零依赖 | 新项目 | ✅ 70+ 解剖区域, 前后视图, 强度0-10渐变, React/Vue/Svelte/原生JS全支持, UMD+ESM, ~29KB min |
| react-muscle-highlighter | `soroojshehryar/react-muscle-highlighter` | React + TS | 较多 | ✅ 男女模型, 前后视图, 强度映射, 仅React, 零依赖(除React) |
| gaining | `devtribal/gaining` | 原生 JS + Chart.js | 小 | ✅ **点击人体部位记录围度**, localStorage, 暗色UI, 最接近需求 |
| human-body-diagram | npm | Vue + d3 | 小 | 中文人体图, 男女童模型, 可缩放, 支持热区点击 |

### 推荐策略

**方案 A（推荐）：基于 `body-muscles` 扩展**
- 直接 `npm install body-muscles` 作为人体 SVG 渲染基础
- 在其上封装围度标注层（BodyPartLabel），添加围度数值、标注线、颜色映射
- 优势：70+ SVG 路径已绘制好，零依赖，原生 JS 兼容
- 工作量：~60% 减少（不用自己画 SVG）

**方案 B：参考 `gaining` 自行实现**
- 克隆 gaining 的交互式人体 SVG 模板和点击逻辑
- 用 TypeScript 重写，添加更丰富的围度展示和数据模型
- 优势：gaining 本身就是围度记录应用，UI/UX 更贴近
- 劣势：需要 TS 重写，维护负担更大

**方案 C：使用 `react-muscle-highlighter` + React**
- 由于现有 console 端已经使用 React，可直接集成
- 优势：React 组件，即插即用
- 劣势：与计划中的"独立可运行"有矛盾，绑定 React

---

## 选定方案：A（基于 body-muscles + 自研围度层）

理由：
1. `body-muscles` 零框架依赖，纯 TS，符合独立运行需求
2. 70+ SVG 区域已定义好，前后视图齐全
3. 强度映射（0-10渐变色）可直接用于围度→颜色映射
4. UMD/ESM 双格式，可直接 `<script>` 引入也可 `import`
5. ~29KB min 非常轻量

---

## 数据模型设计

### 1. BodyMeasurements — 身体围度测量

```typescript
interface BodyMeasurements {
  id: string;
  userId: string;
  measureDate: string;

  // 基础指标
  height: number;                // 身高 (cm)
  weight: number;                // 体重 (kg)

  // 围度测量 (cm)
  neck: number;                  // 颈围
  shoulderWidth: number;         // 肩宽
  chest: number;                 // 胸围
  waist: number;                 // 腰围
  hip: number;                   // 臀围
  leftUpperArm: number;          // 左上臂围
  rightUpperArm: number;         // 右上臂围
  leftForearm: number;           // 左前臂围
  rightForearm: number;          // 右前臂围
  leftThigh: number;             // 左大腿围
  rightThigh: number;            // 右大腿围
  leftCalf: number;              // 左小腿围
  rightCalf: number;             // 右小腿围

  // 体成分
  bodyFat: number;               // 体脂率 (%)
  muscleMass: number;            // 肌肉量 (kg)
  waterPercentage: number;       // 水分率 (%)
  visceralFatLevel: number;      // 内脏脂肪等级 (1-59)
  bmr: number;                   // 基础代谢率 (kcal/day)
  boneMass: number;              // 骨量 (kg)

  createdAt: string;
  updatedAt: string;
}
```

### 2. BodyPartConfig — 部位配置（SVG 映射）

```typescript
interface BodyPartConfig {
  key: keyof BodyMeasurements;
  label: string;                               // 中文标签
  unit: string;                                // 单位
  muscleId: string;                            // 对应 body-muscles 的 MuscleId
  normalRange: [number, number];               // 正常范围
  side: 'left' | 'right' | 'center';          // 人体位置
}
```

### 3. BodyComparison — 数据对比

```typescript
interface BodyComparison {
  current: BodyMeasurements;
  previous: BodyMeasurements | null;
  changes: Partial<Record<keyof BodyMeasurements, number>>;
}
```

### 4. BodyVisualizationConfig — 可视化配置

```typescript
interface BodyVisualizationConfig {
  showLabels: boolean;
  showValues: boolean;
  showNormalRange: boolean;
  highlightAbnormal: boolean;
  colorScheme: 'default' | 'heat' | 'gradient';
  animationEnabled: boolean;
}
```

---

## TypeScript 接口设计

### BodyModel — 数据模型层

```typescript
class BodyModel {
  constructor(data: BodyMeasurements);
  getBMI(): number;
  getBMIStatus(): 'underweight' | 'normal' | 'overweight' | 'obese';
  getWaistToHipRatio(): number;
  getFFMI(): number;
  getBodyPartStatus(key: keyof BodyMeasurements): 'normal' | 'warning' | 'danger';
  getIntensity(key: keyof BodyMeasurements): number;  // 映射为 body-muscles 的 0-10 强度
  compare(other: BodyMeasurements): BodyComparison;
  toJSON(): BodyMeasurements;
  static fromJSON(json: any): BodyModel;
  static defaultMeasurements(): BodyMeasurements;
}
```

### BodyVisualizer — 可视化主类（封装 body-muscles）

```typescript
import { BodyChart, ViewSide } from 'body-muscles';

class BodyVisualizer {
  private chart: BodyChart;
  private model: BodyModel | null;
  private config: BodyVisualizationConfig;
  private labelLayer: HTMLElement;

  constructor(container: HTMLElement, config?: Partial<BodyVisualizationConfig>);
  render(model: BodyModel): void;                      // 渲染完整视图
  update(model: BodyModel): void;                      // 局部更新
  highlight(parts: (keyof BodyMeasurements)[]): void;  // 高亮部位
  setView(side: 'front' | 'back'): void;               // 切换前/后视图
  setConfig(config: Partial<BodyVisualizationConfig>): void;
  destroy(): void;
  on(event: 'partClick' | 'partHover', callback: Function): void;
}
```

### BodyDataAdapter — 数据适配层

```typescript
class BodyDataAdapter {
  static fromHealthMetrics(metrics: HealthMetrics): Partial<BodyMeasurements>;
  static fromAPIResponse(response: any): BodyModel;
  static toAPIPayload(measurements: BodyMeasurements): any;
}
```

---

## 文件结构

```
bodydemo/
├── index.html                    # 独立演示入口
├── package.json                  # 依赖: body-muscles, vite, typescript
├── tsconfig.json
├── vite.config.ts
├── src/
│   ├── main.ts                   # 入口文件
│   ├── models/
│   │   ├── BodyMeasurements.ts   # 数据接口定义
│   │   ├── BodyModel.ts          # 数据模型类（计算逻辑）
│   │   └── BodyPartConfig.ts     # 身体部位→SVG映射配置
│   ├── visualizer/
│   │   ├── BodyVisualizer.ts     # 主可视化类（封装 body-muscles）
│   │   └── LabelOverlay.ts       # 围度标注叠加层
│   ├── adapter/
│   │   └── BodyDataAdapter.ts    # 数据适配器
│   ├── styles/
│   │   ├── body-visualizer.css   # 主布局样式
│   │   ├── label-overlay.css     # 标注叠加层样式
│   │   └── animations.css        # 动画效果
│   └── demo/
│       └── demo-data.ts          # 演示用示例数据
```

---

## 实现步骤

### 步骤 1：项目初始化
- 创建 `bodydemo/` 目录
- `npm init -y` 并安装依赖：`body-muscles`, `vite`, `typescript`
- 配置 `tsconfig.json` 和 `vite.config.ts`
- 创建 `index.html`

### 步骤 2：数据模型层
- 定义 `BodyMeasurements` 接口
- 定义 `BodyPartConfig` + 映射常量（将围度字段映射到 body-muscles 的 MuscleId）
- 实现 `BodyModel` 类（BMI、腰臀比、FFMI、强度映射 0-10）

### 步骤 3：可视化核心
- 实现 `BodyVisualizer`（封装 BodyChart，管理渲染生命周期）
- 实现 `LabelOverlay`（围度标注叠加层：引线 + 数值气泡 + 状态颜色）
- 围度值→颜色/强度映射（正常=蓝绿, 警告=黄, 危险=红）

### 步骤 4：CSS 样式
- `body-visualizer.css`：整体布局（左侧人体 + 右侧面板）
- `label-overlay.css`：标注线、气泡、引线样式
- `animations.css`：过渡动画、悬停效果

### 步骤 5：数据适配层
- 实现 `BodyDataAdapter`（兼容现有 HealthMetrics）
- 准备演示数据（多种体型示例）

### 步骤 6：演示页面
- 左侧：交互式人体可视化（点击部位显示详情，前后视图切换）
- 右侧：数据面板（围度列表 + 对比变化箭头 + 状态标签）
- 底部：控制栏（配色方案、标注开关、历史对比）

### 步骤 7：验证与优化
- 启动 Vite dev server 验证
- TypeScript 类型检查
- 响应式优化

---

## 关键设计决策

1. **基于 body-muscles 扩展**：利用现成 SVG 路径（70+ 区域），专注于围度数据展示逻辑
2. **围度→强度映射**：通过归一化围度值到正常范围，映射为 body-muscles 的 0-10 强度，实现颜色渐变
3. **标注叠加层**：在 body-muscles SVG 之上叠加绝对定位的围度标注，不修改底层 SVG
4. **左右对称展示**：左右臂围/腿围分别在人体对应侧展示
5. **独立可运行**：bodydemo 可 `npm run dev` 独立运行，也可作为模块导入现有项目
