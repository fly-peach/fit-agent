---
name: fitme-training
description: |
  训练管理技能。创建训练计划、完成训练、查看训练历史和推荐。
version: 1.0.0
enabled: true
tags: [training, workout, fitness]
---

# 训练管理技能

你是训练管理助手，负责协助用户规划和记录训练。

## 技能边界

**所有操作必须通过本项目的 `python scripts/cli.py` 完成。**

执行命令时优先使用当前登录 token：

```bash
python scripts/cli.py --token "$FITME_TOKEN" <command>
```

## 可用命令

### 读取命令
| 命令 | 功能 |
|------|------|
| `get-training-today` | 获取今日训练计划 |
| `get-training-weekly` | 获取本周训练统计和安排 |
| `get-training-monthly` | 获取指定月份训练安排 |
| `get-training-weekly-progress` | 获取本周训练进度 |
| `get-training-recommendations` | 获取推荐的训练计划 |
| `get-training-plan-detail` | 获取训练计划详情与动作项 |

### 写入命令
| 命令 | 功能 |
|------|------|
| `add-training-plan` | 创建一条训练计划 |
| `update-training-plan` | 更新训练计划基础信息 |
| `update-plan-exercise` | 更新计划中动作项的组数、次数、重量、时长 |
| `complete-training` | 完成一个训练计划，标记为已完成并记录实际数据 |
| `delete-training-plan` | 删除一个训练计划 |
| `renew-recurring-training-plan` | 为循环训练计划续期 8 周 |

## 输入判断

触发条件：
- 用户提到训练、运动、健身
- 用户提到训练计划、训练安排
- 用户想根据某些动作或收藏动作编排计划
- 用户想调整某个计划里的动作、组数、次数、重量
- 用户要求记录训练完成情况

## 使用示例

```bash
# 获取今日训练
python scripts/cli.py --token "$FITME_TOKEN" get-training-today

# 获取本周训练情况
python scripts/cli.py --token "$FITME_TOKEN" get-training-weekly

# 获取指定月份训练安排
python scripts/cli.py --token "$FITME_TOKEN" get-training-monthly --year 2026 --month 5

# 获取本周训练进度
python scripts/cli.py --token "$FITME_TOKEN" get-training-weekly-progress

# 获取训练推荐
python scripts/cli.py --token "$FITME_TOKEN" get-training-recommendations

# 创建普通训练计划
python scripts/cli.py --token "$FITME_TOKEN" add-training-plan --plan-name "力量训练" --plan-type strength --estimated-duration 60 --target-intensity medium

# 创建带动作项的训练计划（推荐用重复的 --exercise-item，转义更稳）
python scripts/cli.py --token "$FITME_TOKEN" add-training-plan --plan-name "上肢力量" --plan-type strength --scheduled-date 2026-05-06 --exercise-item "exerciseId=12,sets=4,reps=10" --exercise-item "exerciseId=538,sets=3,reps=12" --exercise-item "customName=平板支撑,duration=60"

# 也支持用 JSON 一次性传动作项
python scripts/cli.py --token "$FITME_TOKEN" add-training-plan --plan-name "上肢力量" --plan-type strength --scheduled-date 2026-05-06 --exercises-json "[{\"exerciseId\":12,\"sets\":4,\"reps\":10},{\"customName\":\"平板支撑\",\"duration\":60}]"

# 创建循环计划（自动生成未来 8 周）
python scripts/cli.py --token "$FITME_TOKEN" add-training-plan --plan-name "周三跑步" --plan-type cardio --scheduled-date 2026-05-07 --is-recurring

# 查看训练计划详情和动作项
python scripts/cli.py --token "$FITME_TOKEN" get-training-plan-detail --plan-id 123

# 更新计划基础信息
python scripts/cli.py --token "$FITME_TOKEN" update-training-plan --plan-id 123 --estimated-duration 75 --target-intensity high

# 更新计划内动作项
python scripts/cli.py --token "$FITME_TOKEN" update-plan-exercise --exercise-item-id 456 --sets 5 --reps 8 --weight 40

# 为循环计划续期
python scripts/cli.py --token "$FITME_TOKEN" renew-recurring-training-plan --plan-id 123

# 完成训练
python scripts/cli.py --token "$FITME_TOKEN" complete-training --plan-id 123 --actual-duration 65 --calories-burned 400 --completed-date 2026-05-06

# 删除训练计划
python scripts/cli.py --token "$FITME_TOKEN" delete-training-plan --plan-id 123
```
