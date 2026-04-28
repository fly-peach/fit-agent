import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Statistic, Progress, List, Avatar, Tag, Skeleton } from 'antd'
import {
  FireOutlined,
  TrophyOutlined,
  HeartOutlined,
  CoffeeOutlined,
} from '@ant-design/icons'
import { healthApi, type HealthMetrics } from '../../services/health'
import { trainingApi, type WeeklyStats, TrainingSchedule } from '../../services/training'
import { dietApi, type DietStats } from '../../services/diet'

const Dashboard: React.FC = () => {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null)
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [dietStats, setDietStats] = useState<DietStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [health, stats, diet, sched] = await Promise.all([
        healthApi.getMetrics(),
        trainingApi.getWeeklyStats(),
        dietApi.getTodayStats(),
        trainingApi.getWeeklySchedule(),
      ])
      setHealthMetrics(health)
      setWeeklyStats(stats)
      setDietStats(diet)
      setSchedule(sched)
    } finally {
      setLoading(false)
    }
  }

  const getProgressPercent = (current: number, goal: number) => {
    if (!goal) return 0
    return Math.round((current / goal) * 100)
  }

  const getTypeTag = (type: string) => {
    const colors: Record<string, string> = {
      strength: 'orange',
      cardio: 'green',
      flexibility: 'blue',
    }
    const labels: Record<string, string> = { strength: '力量', cardio: '有氧', flexibility: '柔韧' }
    return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>
  }

  const getStatusTag = (status: string) => {
    if (status === 'completed') return <Tag color="success">已完成</Tag>
    return <Tag color="processing">待完成</Tag>
  }

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>📊 今日概览</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={<><FireOutlined /> 本周训练</>}
              value={weeklyStats?.weeklyCount || 0}
              suffix="次"
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress
              percent={weeklyStats ? getProgressPercent(weeklyStats.completedCount, weeklyStats.weeklyCount) : 0}
              strokeColor="#52c41a"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={<><CoffeeOutlined /> 今日卡路里</>}
              value={dietStats?.remainingCalories || 0}
              suffix="kcal"
              valueStyle={{ color: '#ff4d4f' }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              已摄入 {dietStats?.calories || 0} / {dietStats?.caloriesGoal || 2000} kcal
            </Typography.Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={<><TrophyOutlined /> 连续训练</>}
              value={weeklyStats?.streakDays || 0}
              suffix="天"
              valueStyle={{ color: '#722ed1' }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>继续保持！</Typography.Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={<><HeartOutlined /> 当前体重</>}
              value={healthMetrics?.weight || 0}
              suffix="kg"
            />
            {healthMetrics?.weightGoal && (
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                目标 {healthMetrics.weightGoal} kg
              </Typography.Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="本周训练安排">
            <List
              itemLayout="horizontal"
              dataSource={schedule.slice(0, 5)}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar style={{ backgroundColor: item.status === 'completed' ? '#52c41a' : '#1890ff' }}>
                        {item.status === 'completed' ? '✓' : item.dayOfWeek}
                      </Avatar>
                    }
                    title={item.planName}
                    description={`${item.duration}分钟 · ${item.intensity}强度`}
                  />
                  <div style={{ display: 'flex', gap: 4 }}>
                    {getTypeTag(item.planType)}
                    {getStatusTag(item.status)}
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="今日营养摄入">
            <div style={{ marginTop: 16 }}>
              <Typography.Text>蛋白质</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.protein || 0, dietStats?.proteinGoal || 150)}
                strokeColor="#52c41a"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>碳水</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.carbs || 0, dietStats?.carbsGoal || 250)}
                strokeColor="#faad14"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>脂肪</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.fat || 0, dietStats?.fatGoal || 65)}
                strokeColor="#ff4d4f"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>饮水</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.water || 0, dietStats?.waterGoal || 2000)}
                strokeColor="#1890ff"
              />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
