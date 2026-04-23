# FitAgent 数据库设计文档

## 数据库表结构

### 1. 用户表 (users)

```sql
CREATE TABLE users (
    user_id          INT PRIMARY KEY AUTO_INCREMENT,
    name             VARCHAR(50) NOT NULL COMMENT '用户姓名',
    email            VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    password_hash    VARCHAR(255) NOT NULL COMMENT '密码哈希',
    avatar           VARCHAR(10) DEFAULT NULL COMMENT '头像字母/颜色',
    role             VARCHAR(20) DEFAULT 'user' COMMENT '角色: admin/user',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at       DATETIME DEFAULT NULL COMMENT '软删除时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';
```

### 2. 用户设置表 (user_settings)

```sql
CREATE TABLE user_settings (
    setting_id       INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL UNIQUE,
    calorie_goal     INT DEFAULT 2000 COMMENT '每日卡路里目标',
    protein_goal     INT DEFAULT 150 COMMENT '每日蛋白质目标(g)',
    carbs_goal       INT DEFAULT 250 COMMENT '每日碳水目标(g)',
    fat_goal         INT DEFAULT 65 COMMENT '每日脂肪目标(g)',
    water_goal       INT DEFAULT 2000 COMMENT '每日饮水目标(ml)',
    weight_goal      DECIMAL(5,2) DEFAULT NULL COMMENT '目标体重(kg)',
    weekly_training_goal INT DEFAULT 5 COMMENT '每周训练目标次数',
    notification_enabled BOOLEAN DEFAULT TRUE COMMENT '是否开启通知',
    reminder_time    TIME DEFAULT '07:00:00' COMMENT '提醒时间',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户设置表';
```

### 3. 健康指标记录表 (health_metrics)

```sql
CREATE TABLE health_metrics (
    record_id        INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,
    weight           DECIMAL(5,2) COMMENT '体重(kg)',
    height           DECIMAL(5,2) COMMENT '身高(cm)',
    body_fat         DECIMAL(4,2) COMMENT '体脂率(%)',
    bmi              DECIMAL(4,2) COMMENT 'BMI指数',
    bmi_status       VARCHAR(10) DEFAULT 'normal' COMMENT 'BMI状态: normal/under/over',
    measure_date     DATE NOT NULL COMMENT '测量日期',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_date (user_id, measure_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='健康指标记录表';
```

### 4. 训练计划表 (training_plans)

```sql
CREATE TABLE training_plans (
    plan_id          INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,
    plan_name        VARCHAR(100) NOT NULL COMMENT '计划名称',
    plan_type        VARCHAR(20) NOT NULL COMMENT '训练类型: strength/cardio/flexibility',
    target_intensity VARCHAR(20) DEFAULT 'medium' COMMENT '目标强度: low/medium/high',
    estimated_duration INT DEFAULT 60 COMMENT '预计时长(分钟)',
    scheduled_date   DATE NOT NULL COMMENT '计划日期',
    day_of_week      INT COMMENT '周几(1-7)',
    status           VARCHAR(20) DEFAULT 'pending' COMMENT '状态: pending/completed/cancelled',
    note             TEXT COMMENT '备注',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_date (user_id, scheduled_date),
    INDEX idx_user_status (user_id, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练计划表';
```

### 5. 训练完成记录表 (training_records)

```sql
CREATE TABLE training_records (
    record_id        INT PRIMARY KEY AUTO_INCREMENT,
    plan_id          INT NOT NULL,
    user_id          INT NOT NULL,
    actual_duration  INT COMMENT '实际时长(分钟)',
    actual_intensity VARCHAR(20) COMMENT '实际强度',
    calories_burned  INT COMMENT '消耗卡路里',
    completed_at     DATETIME NOT NULL COMMENT '完成时间',
    note             TEXT COMMENT '训练备注',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_id) REFERENCES training_plans(plan_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_date (user_id, completed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='训练完成记录表';
```

### 6. 饮食记录表 (diet_meals)

```sql
CREATE TABLE diet_meals (
    meal_id          INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,
    meal_type        VARCHAR(20) NOT NULL COMMENT '餐类型: breakfast/lunch/dinner/snack',
    meal_name        VARCHAR(100) NOT NULL COMMENT '食物名称',
    calories         INT NOT NULL COMMENT '卡路里',
    protein          DECIMAL(6,2) DEFAULT 0 COMMENT '蛋白质(g)',
    carbs            DECIMAL(6,2) DEFAULT 0 COMMENT '碳水(g)',
    fat              DECIMAL(6,2) DEFAULT 0 COMMENT '脂肪(g)',
    water            INT DEFAULT 0 COMMENT '饮水量(ml)',
    meal_date        DATE NOT NULL COMMENT '日期',
    meal_time        TIME NOT NULL COMMENT '时间',
    note             TEXT COMMENT '备注',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_date (user_id, meal_date),
    INDEX idx_user_type (user_id, meal_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='饮食记录表';
```

### 7. 饮食目标日志表 (diet_goals_log)

```sql
CREATE TABLE diet_goals_log (
    log_id           INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,
    log_date         DATE NOT NULL COMMENT '日期',
    calorie_goal     INT COMMENT '当日卡路里目标',
    protein_goal     INT COMMENT '当日蛋白质目标',
    carbs_goal       INT COMMENT '当日碳水目标',
    fat_goal         INT COMMENT '当日脂肪目标',
    water_goal       INT COMMENT '当日饮水目标',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY uk_user_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='饮食目标日志表(记录每日目标变化)';
```

### 8. 推荐训练计划表 (recommended_trainings)

```sql
CREATE TABLE recommended_trainings (
    recommend_id     INT PRIMARY KEY AUTO_INCREMENT,
    plan_name        VARCHAR(100) NOT NULL COMMENT '计划名称',
    plan_type        VARCHAR(20) NOT NULL COMMENT '类型: strength/cardio/flexibility',
    duration         INT NOT NULL COMMENT '时长(分钟)',
    intensity        VARCHAR(20) NOT NULL COMMENT '强度: low/medium/high',
    calories_burn    INT COMMENT '预计消耗卡路里',
    description      TEXT COMMENT '描述',
    target_body_type VARCHAR(50) COMMENT '适用体型',
    difficulty_level VARCHAR(20) DEFAULT 'medium' COMMENT '难度: beginner/intermediate/advanced',
    is_active        BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推荐训练计划表';
```

### 9. 推荐食物表 (recommended_foods)

```sql
CREATE TABLE recommended_foods (
    recommend_id     INT PRIMARY KEY AUTO_INCREMENT,
    food_name        VARCHAR(100) NOT NULL COMMENT '食物名称',
    calories         INT NOT NULL COMMENT '卡路里(每100g)',
    protein          DECIMAL(6,2) COMMENT '蛋白质(g)',
    carbs            DECIMAL(6,2) COMMENT '碳水(g)',
    fat              DECIMAL(6,2) COMMENT '脂肪(g)',
    reason           VARCHAR(200) COMMENT '推荐理由',
    suitable_time    VARCHAR(50) COMMENT '适合时段: breakfast/lunch/dinner/snack/any',
    category         VARCHAR(50) COMMENT '分类: meat/vegetable/fruit/grain/dairy',
    is_active        BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推荐食物表';
```

### 10. 连续记录统计表 (streak_stats)

```sql
CREATE TABLE streak_stats (
    streak_id        INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL UNIQUE,
    training_streak  INT DEFAULT 0 COMMENT '连续训练天数',
    diet_streak      INT DEFAULT 0 COMMENT '连续饮食记录天数',
    last_training_date DATE COMMENT '最后一次训练日期',
    last_diet_date   DATE COMMENT '最后一次饮食记录日期',
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='连续记录统计表';
```

### 11. 每日饮食统计汇总表 (daily_diet_summary)

```sql
CREATE TABLE daily_diet_summary (
    summary_id       INT PRIMARY KEY AUTO_INCREMENT,
    user_id          INT NOT NULL,
    summary_date     DATE NOT NULL,
    total_calories   INT DEFAULT 0 COMMENT '总卡路里',
    total_protein    DECIMAL(6,2) DEFAULT 0 COMMENT '总蛋白质',
    total_carbs      DECIMAL(6,2) DEFAULT 0 COMMENT '总碳水',
    total_fat        DECIMAL(6,2) DEFAULT 0 COMMENT '总脂肪',
    total_water      INT DEFAULT 0 COMMENT '总饮水量',
    protein_goal_met BOOLEAN DEFAULT FALSE COMMENT '蛋白质达标',
    water_goal_met   BOOLEAN DEFAULT FALSE COMMENT '饮水达标',
    meal_count       INT DEFAULT 0 COMMENT '餐次数量',
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY uk_user_date (user_id, summary_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='每日饮食统计汇总表';
```

---

## 数据库关系图

```
┌─────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│   users     │────<│   user_settings │     │   streak_stats      │
│             │     │                 │     │                     │
│  user_id(PK)│────<│  user_id(FK/UK) │     │  user_id(FK/UK)     │
│  name       │     │  calorie_goal   │     │  training_streak    │
│  email      │     │  protein_goal   │     │  diet_streak        │
│  password   │     │  ...            │     │                     │
└─────────────┘     └─────────────────┘     └─────────────────────┘
       │
       │
       ├──────────────────────────────────────────────────────┐
       │                      │                               │
       ▼                      ▼                               ▼
┌─────────────────┐  ┌─────────────────┐            ┌─────────────────┐
│ health_metrics  │  │  diet_meals     │            │ training_plans  │
│                 │  │                 │            │                 │
│ record_id(PK)   │  │ meal_id(PK)     │            │ plan_id(PK)     │
│ user_id(FK)     │  │ user_id(FK)     │            │ user_id(FK)     │
│ weight          │  │ meal_type       │            │ plan_name       │
│ body_fat        │  │ meal_name       │            │ plan_type       │
│ bmi             │  │ calories        │            │ scheduled_date  │
│ measure_date    │  │ protein/carbs/  │            │ status          │
│                 │  │ fat/water       │            │                 │
└─────────────────┘  │ meal_date       │            └─────────────────┘
                     │ meal_time       │                    │
                     └─────────────────┘                    │
                            │                               ▼
                            ▼                    ┌─────────────────┐
                    ┌─────────────────┐          │training_records │
                    │daily_diet_summary│         │                 │
                    │                 │          │ record_id(PK)   │
                    │ summary_id(PK)  │          │ plan_id(FK)     │
                    │ user_id(FK)     │          │ user_id(FK)     │
                    │ summary_date(UK)│          │ actual_duration │
                    │ total_calories  │          │ calories_burned │
                    │ protein_goal_met│          │ completed_at    │
                    └─────────────────┘          └─────────────────┘
```

---

## 索引设计说明

| 表名 | 索引名 | 字段 | 说明 |
|------|--------|------|------|
| health_metrics | idx_user_date | user_id, measure_date | 查询用户某日期的健康数据 |
| training_plans | idx_user_date | user_id, scheduled_date | 查询用户某日期的训练计划 |
| training_plans | idx_user_status | user_id, status | 查询用户待完成/已完成的计划 |
| training_records | idx_user_date | user_id, completed_at | 查询用户训练历史 |
| diet_meals | idx_user_date | user_id, meal_date | 查询用户某日期的饮食记录 |
| diet_meals | idx_user_type | user_id, meal_type | 查询用户某类型餐次 |
| diet_goals_log | uk_user_date | user_id, log_date | 每用户每天一条目标记录 |
| daily_diet_summary | uk_user_date | user_id, summary_date | 每用户每天一条汇总 |

---

## 初始化数据

```sql
-- 默认推荐训练计划
INSERT INTO recommended_trainings (plan_name, plan_type, duration, intensity, calories_burn, description) VALUES
('HIIT燃脂', 'cardio', 30, 'high', 400, '高强度间歇训练，快速燃脂'),
('瑜伽放松', 'flexibility', 45, 'low', 150, '放松身心，提高柔韧性'),
('力量训练-上肢', 'strength', 60, 'medium', 300, '专注上肢肌肉训练'),
('力量训练-下肢', 'strength', 60, 'medium', 350, '腿部和臀部训练'),
('跑步', 'cardio', 45, 'medium', 400, '有氧跑步训练');

-- 默认推荐食物
INSERT INTO recommended_foods (food_name, calories, protein, carbs, fat, reason, suitable_time, category) VALUES
('鸡胸肉', 165, 31, 0, 3.6, '高蛋白低脂肪，增肌首选', 'lunch', 'meat'),
('三文鱼', 208, 20, 0, 13, '富含Omega-3，有益心血管', 'lunch', 'meat'),
('燕麦', 389, 16.9, 66, 6.9, '优质碳水，饱腹感强', 'breakfast', 'grain'),
('鸡蛋', 155, 13, 1.1, 11, '完整蛋白质来源', 'breakfast', 'protein'),
('西兰花', 34, 2.8, 7, 0.4, '低卡高纤维蔬菜', 'lunch', 'vegetable'),
('苹果', 52, 0.3, 14, 0.2, '健康零食，补充维生素', 'snack', 'fruit');
```

---

## 数据库选型建议

- **主数据库**: MySQL 8.0+ 或 PostgreSQL 14+
- **缓存**: Redis (用于session、统计数据缓存)
- **特点**:
  - 用户量预估中等规模，单库可满足
  - 饮食/训练记录写入频繁，建议定期归档历史数据
  - 统计数据可考虑使用Redis缓存减少查询压力