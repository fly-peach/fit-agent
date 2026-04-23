# FitAgent 后端接口文档

## 1. 用户模块

### 1.1 用户信息
```
GET /api/user/profile
Response:
{
  "code": 200,
  "data": {
    "userId": 1,
    "name": "健身达人",
    "email": "fitness@email.com",
    "avatar": "J",
    "role": "管理员",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### 1.2 更新用户信息
```
PUT /api/user/profile
Request:
{
  "name": "健身达人",
  "avatar": "J"
}
Response:
{
  "code": 200,
  "message": "更新成功"
}
```

---

## 2. 健康数据模块 (Dashboard)

### 2.1 获取用户基础指标
```
GET /api/health/metrics
Response:
{
  "code": 200,
  "data": {
    "weight": 68,           // 体重 (kg)
    "height": 175,          // 身高 (cm)
    "bodyFat": 15.5,        // 体脂率 (%)
    "bmi": 22.0,            // BMI指数
    "weightGoal": 65,       // 体重目标
    "bmiStatus": "normal"   // BMI状态: normal/under/over
  }
}
```

### 2.2 更新基础指标
```
POST /api/health/metrics
Request:
{
  "weight": 68,
  "bodyFat": 15.5,
  "measureDate": "2024-04-23"
}
Response:
{
  "code": 200,
  "message": "记录成功",
  "data": {
    "recordId": 123,
    "createdAt": "2024-04-23T10:30:00Z"
  }
}
```

### 2.3 获取历史测量记录
```
GET /api/health/measurements?limit=10
Response:
{
  "code": 200,
  "data": [
    {
      "recordId": 1,
      "weight": 68,
      "bodyFat": 15.5,
      "bmi": 22.0,
      "measureDate": "2024-04-23",
      "createdAt": "2024-04-23T10:30:00Z"
    }
  ]
}
```

### 2.4 获取健康数据报表
```
GET /api/health/report?period=week&status=all
参数:
  - period: week/month/year (时间周期)
  - status: all/pass/low/high (筛选状态)

Response:
{
  "code": 200,
  "data": {
    "weightTrend": [
      { "date": "2024-04-17", "value": 68.5 },
      { "date": "2024-04-18", "value": 68.3 },
      { "date": "2024-04-19", "value": 68.0 },
      { "date": "2024-04-20", "value": 68.2 },
      { "date": "2024-04-21", "value": 67.8 },
      { "date": "2024-04-22", "value": 68.0 },
      { "date": "2024-04-23", "value": 68.0 }
    ],
    "bmiTrend": [
      { "date": "2024-04-17", "value": 22.1 },
      { "date": "2024-04-23", "value": 22.0 }
    ],
    "summary": {
      "avgWeight": 68.0,
      "avgBmi": 22.0,
      "weightChange": -0.5,
      "statusSummary": {
        "pass": 5,
        "low": 1,
        "high": 1
      }
    }
  }
}
```

### 2.5 导出健康数据
```
GET /api/health/export?period=week&format=csv
Response: 文件下载 (CSV/Excel)
```

---

## 3. 训练计划模块 (Fitness)

### 3.1 获取本周训练统计
```
GET /api/training/stats/weekly
Response:
{
  "code": 200,
  "data": {
    "weeklyCount": 5,           // 本周训练次数
    "weeklyHours": 8.5,         // 本周训练时长 (小时)
    "weeklyCalories": 2400,     // 本周消耗卡路里
    "streakDays": 18,           // 连续训练天数
    "completedCount": 4,        // 已完成次数
    "remainingCount": 1         // 剩余次数
  }
}
```

### 3.2 获取本周训练安排
```
GET /api/training/schedule/weekly
Response:
{
  "code": 200,
  "data": [
    {
      "dayOfWeek": 1,           // 周一
      "date": "2024-04-22",
      "planName": "力量训练",
      "planType": "strength",   // strength/cardio/flexibility
      "duration": 60,           // 分钟
      "intensity": "medium",    // low/medium/high
      "status": "completed",
      "completedAt": "2024-04-22T07:30:00Z"
    },
    {
      "dayOfWeek": 2,
      "date": "2024-04-23",
      "planName": "跑步",
      "planType": "cardio",
      "duration": 45,
      "intensity": "medium",
      "status": "pending"
    }
  ]
}
```

### 3.3 获取本周进度
```
GET /api/training/progress/weekly
Response:
{
  "code": 200,
  "data": {
    "targetCount": 5,
    "completedCount": 4,
    "progressPercent": 80,
    "daysProgress": [
      { "day": "周一", "completed": true },
      { "day": "周二", "completed": true },
      { "day": "周三", "completed": true },
      { "day": "周四", "completed": true },
      { "day": "周五", "completed": false }
    ]
  }
}
```

### 3.4 获取推荐训练计划
```
GET /api/training/recommendations
Response:
{
  "code": 200,
  "data": [
    {
      "recommendId": 1,
      "planName": "HIIT燃脂",
      "planType": "cardio",
      "duration": 30,
      "intensity": "high",
      "caloriesBurn": 400,
      "suitability": "high"     // 与用户匹配度
    },
    {
      "recommendId": 2,
      "planName": "瑜伽放松",
      "planType": "flexibility",
      "duration": 45,
      "intensity": "low",
      "caloriesBurn": 150
    }
  ]
}
```

### 3.5 创建训练计划
```
POST /api/training/plans
Request:
{
  "planName": "力量训练",
  "planType": "strength",       // strength/cardio/flexibility
  "targetIntensity": "medium",  // low/medium/high
  "estimatedDuration": 60,      // 分钟
  "scheduledDate": "2024-04-24",
  "note": "专注上肢训练"
}
Response:
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "planId": 100
  }
}
```

### 3.6 更新训练计划
```
PUT /api/training/plans/{planId}
Request:
{
  "planName": "力量训练-修改",
  "scheduledDate": "2024-04-25"
}
Response:
{
  "code": 200,
  "message": "更新成功"
}
```

### 3.7 完成训练记录
```
POST /api/training/complete/{planId}
Request:
{
  "actualDuration": 65,        // 实际时长
  "actualIntensity": "medium",
  "caloriesBurned": 350,
  "note": "今天感觉不错"
}
Response:
{
  "code": 200,
  "message": "记录成功"
}
```

### 3.8 删除训练计划
```
DELETE /api/training/plans/{planId}
Response:
{
  "code": 200,
  "message": "删除成功"
}
```

---

## 4. 饮食管理模块 (Diet)

### 4.1 获取今日饮食统计
```
GET /api/diet/stats/today
Response:
{
  "code": 200,
  "data": {
    "calories": 1450,          // 已摄入卡路里
    "caloriesGoal": 2000,      // 目标卡路里
    "remainingCalories": 550,
    "protein": 120,            // 蛋白质 (g)
    "proteinGoal": 150,
    "carbs": 180,              // 碳水 (g)
    "carbsGoal": 250,
    "fat": 48,                 // 脂肪 (g)
    "fatGoal": 65,
    "water": 1200,             // 饮水量 (ml)
    "waterGoal": 2000,
    "streakDays": 18           // 连续记录天数
  }
}
```

### 4.2 获取今日饮食记录
```
GET /api/diet/meals/today
Response:
{
  "code": 200,
  "data": [
    {
      "mealId": 1,
      "mealType": "breakfast",   // breakfast/lunch/dinner/snack
      "mealName": "燕麦牛奶+鸡蛋",
      "calories": 350,
      "protein": 15,
      "carbs": 45,
      "fat": 12,
      "time": "07:30",
      "note": ""
    },
    {
      "mealId": 2,
      "mealType": "lunch",
      "mealName": "鸡胸肉沙拉",
      "calories": 450,
      "protein": 35,
      "carbs": 30,
      "fat": 15,
      "time": "12:00"
    }
  ]
}
```

### 4.3 添加饮食记录
```
POST /api/diet/meals
Request:
{
  "mealType": "snack",        // breakfast/lunch/dinner/snack
  "mealName": "苹果",
  "calories": 80,
  "protein": 0,
  "carbs": 20,
  "fat": 0,
  "water": 0,
  "time": "15:00",
  "note": "下午加餐"
}
Response:
{
  "code": 200,
  "message": "添加成功",
  "data": {
    "mealId": 5
  }
}
```

### 4.4 更新饮食记录
```
PUT /api/diet/meals/{mealId}
Request:
{
  "mealName": "修改后的名称",
  "calories": 100
}
Response:
{
  "code": 200,
  "message": "更新成功"
}
```

### 4.5 删除饮食记录
```
DELETE /api/diet/meals/{mealId}
Response:
{
  "code": 200,
  "message": "删除成功"
}
```

### 4.6 获取营养摄入进度
```
GET /api/diet/nutrition/progress
Response:
{
  "code": 200,
  "data": {
    "protein": { "current": 120, "goal": 150, "percent": 80 },
    "carbs": { "current": 180, "goal": 250, "percent": 72 },
    "fat": { "current": 48, "goal": 65, "percent": 74 }
  }
}
```

### 4.7 获取推荐食物
```
GET /api/diet/recommendations
Response:
{
  "code": 200,
  "data": [
    {
      "recommendId": 1,
      "foodName": "鸡胸肉",
      "calories": 165,
      "protein": 31,
      "reason": "高蛋白低脂肪",
      "suitableTime": "lunch"
    },
    {
      "recommendId": 2,
      "foodName": "三文鱼",
      "calories": 208,
      "protein": 20,
      "reason": "富含Omega-3"
    }
  ]
}
```

### 4.8 获取本周饮食趋势
```
GET /api/diet/trend/weekly
Response:
{
  "code": 200,
  "data": {
    "dailyStats": [
      { 
        "day": "周一", 
        "date": "2024-04-17",
        "calories": 1820, 
        "proteinGoalMet": true, 
        "waterGoalMet": true 
      },
      { 
        "day": "周二", 
        "date": "2024-04-18",
        "calories": 1750, 
        "proteinGoalMet": true, 
        "waterGoalMet": true 
      }
    ],
    "summary": {
      "avgCalories": 1820,
      "proteinGoalDays": 5,
      "waterGoalDays": 6
    }
  }
}
```

---

## 5. 用户设置模块

### 5.1 获取用户设置
```
GET /api/user/settings
Response:
{
  "code": 200,
  "data": {
    "calorieGoal": 2000,
    "proteinGoal": 150,
    "carbsGoal": 250,
    "fatGoal": 65,
    "waterGoal": 2000,
    "weightGoal": 65,
    "weeklyTrainingGoal": 5,
    "notificationEnabled": true,
    "reminderTime": "07:00"
  }
}
```

### 5.2 更新用户设置
```
PUT /api/user/settings
Request:
{
  "calorieGoal": 1800,
  "weeklyTrainingGoal": 4
}
Response:
{
  "code": 200,
  "message": "更新成功"
}
```

---

## 6. 认证模块

### 6.1 登录
```
POST /api/auth/login
Request:
{
  "email": "admin@fitagent.com",
  "password": "password123"
}
Response:
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "userId": 1,
      "name": "Admin",
      "email": "admin@fitagent.com",
      "role": "管理员"
    }
  }
}
```

### 6.2 登出
```
POST /api/auth/logout
Response:
{
  "code": 200,
  "message": "登出成功"
}
```

---

## 通用响应格式

```json
{
  "code": 200,          // 状态码: 200成功, 400参数错误, 401未授权, 500服务器错误
  "message": "success", // 提示信息
  "data": {}            // 返回数据
}
```

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未授权/登录过期 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |