import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Statistic, Progress, List, Avatar, Tag, Skeleton } from 'antd'
import {
  FireOutlined,
  TrophyOutlined,
  CoffeeOutlined,
} from '@ant-design/icons'
import { LayoutDashboard } from 'lucide-react'
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
    const colors: Record<string, string> = { strength: '#F59E0B', cardio: '#10B981', flexibility: '#0EA5E9' }
    const labels: Record<string, string> = { strength: '力量', cardio: '有氧', flexibility: '柔韧' }
    return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>
  }

  const getStatusTag = (status: string) => {
    if (status === 'completed') return <Tag color="#10B981">已完成</Tag>
    return <Tag color="#06B6D4">待完成</Tag>
  }

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Skeleton active />
      </div>
    )
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#E0F2FE', color: '#0EA5E9' }}>
          <LayoutDashboard size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>今日概览</Typography.Title>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%)' }}>
            <Statistic
              title={<><FireOutlined style={{ color: '#0EA5E9' }} /> 本周训练</>}
              value={weeklyStats?.weeklyCount || 0}
              suffix="次"
              valueStyle={{ color: '#0EA5E9', fontWeight: 700 }}
            />
            <Progress
              percent={weeklyStats ? getProgressPercent(weeklyStats.completedCount, weeklyStats.weeklyCount) : 0}
              strokeColor="#0EA5E9"
              style={{ marginTop: 8 }}
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #ECFEFF 0%, #CFFAFE 100%)' }}>
            <Statistic
              title={<><CoffeeOutlined style={{ color: '#06B6D4' }} /> 今日卡路里</>}
              value={dietStats?.remainingCalories || 0}
              suffix="kcal"
              valueStyle={{ color: '#06B6D4', fontWeight: 700 }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              已摄入 {dietStats?.calories || 0} / {dietStats?.caloriesGoal || 2000} kcal
            </Typography.Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)' }}>
            <Statistic
              title={<><TrophyOutlined style={{ color: '#8B5CF6' }} /> 连续训练</>}
              value={weeklyStats?.streakDays || 0}
              suffix="天"
              valueStyle={{ color: '#8B5CF6', fontWeight: 700 }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>继续保持！</Typography.Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)' }}>
            <Statistic
              title={<span style={{ color: '#10B981' }}>&#10084;&#65039; 当前体重</span>}
              value={healthMetrics?.weight || 0}
              suffix="kg"
              valueStyle={{ fontWeight: 700 }}
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
          <Card title="本周训练安排" style={{ border: 'none' }}>
            <List
              itemLayout="horizontal"
              dataSource={schedule.slice(0, 5)}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar style={{ backgroundColor: item.status === 'completed' ? '#10B981' : '#0EA5E9' }}>
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
          <Card title="今日营养摄入" style={{ border: 'none' }}>
            <div style={{ marginTop: 16 }}>
              <Typography.Text>蛋白质</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.protein || 0, dietStats?.proteinGoal || 150)}
                strokeColor="#10B981"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>碳水</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.carbs || 0, dietStats?.carbsGoal || 250)}
                strokeColor="#F59E0B"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>脂肪</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.fat || 0, dietStats?.fatGoal || 65)}
                strokeColor="#EF4444"
                style={{ marginBottom: 8 }}
              />
              <Typography.Text>饮水</Typography.Text>
              <Progress
                percent={getProgressPercent(dietStats?.water || 0, dietStats?.waterGoal || 2000)}
                strokeColor="#0EA5E9"
              />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
