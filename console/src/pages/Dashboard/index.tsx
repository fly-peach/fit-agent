import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Progress, List, Tag, Avatar, Typography } from 'antd'
import {
  FireOutlined,
  HeartOutlined,
  ThunderboltOutlined,
  TrophyOutlined,
  DashboardOutlined,
} from '@ant-design/icons'
import { healthApi, type HealthMetrics } from '../../services/health'
import { trainingApi, type WeeklyStats, TrainingSchedule } from '../../services/training'
import { dietApi, type DietStats } from '../../services/diet'
import styles from './Dashboard.module.css'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null)
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [dietStats, setDietStats] = useState<DietStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
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
    fetchData()
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'pending':
        return 'blue'
      case 'cancelled':
        return 'red'
      default:
        return 'default'
    }
  }

  const getPlanTypeTag = (type: string) => {
    switch (type) {
      case 'strength':
        return <Tag color="orange">力量</Tag>
      case 'cardio':
        return <Tag color="green">有氧</Tag>
      case 'flexibility':
        return <Tag color="purple">柔韧</Tag>
      default:
        return <Tag>{type}</Tag>
    }
  }

  return (
    <div className={styles.container}>
      <Title level={3}>
        <DashboardOutlined /> 今日概览
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="本周训练"
              value={weeklyStats?.weeklyCount || 0}
              suffix="次"
              prefix={<FireOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
            <Progress
              percent={
                weeklyStats
                  ? Math.round((weeklyStats.completedCount / weeklyStats.weeklyCount) * 100)
                  : 0
              }
              size="small"
              status="active"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="今日卡路里"
              value={dietStats?.remainingCalories || 0}
              suffix="kcal 剩余"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
            <Text type="secondary">
              已摄入 {dietStats?.calories || 0} / {dietStats?.caloriesGoal || 2000} kcal
            </Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="连续训练"
              value={weeklyStats?.streakDays || 0}
              suffix="天"
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <Text type="secondary">继续保持！</Text>
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="当前体重"
              value={healthMetrics?.weight || 0}
              suffix="kg"
              prefix={<HeartOutlined />}
            />
            {healthMetrics?.weightGoal && (
              <Text type="secondary">
                目标 {healthMetrics.weightGoal} kg
              </Text>
            )}
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={12}>
          <Card title="本周训练安排" loading={loading}>
            <List
              dataSource={schedule}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        style={{
                          backgroundColor: item.status === 'completed' ? '#52c41a' : '#1890ff',
                        }}
                      >
                        {item.dayOfWeek}
                      </Avatar>
                    }
                    title={item.planName}
                    description={`${item.duration}分钟 · ${item.intensity}强度`}
                  />
                  <div>
                    {getPlanTypeTag(item.planType)}
                    <Tag color={getStatusColor(item.status)}>
                      {item.status === 'completed' ? '已完成' : '待完成'}
                    </Tag>
                  </div>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="今日营养摄入" loading={loading}>
            <div className={styles.nutrition}>
              <div className={styles.nutrientItem}>
                <Text>蛋白质</Text>
                <Progress
                  percent={dietStats ? Math.round((dietStats.protein / dietStats.proteinGoal) * 100) : 0}
                  format={() => `${dietStats?.protein || 0}/${dietStats?.proteinGoal || 150}g`}
                  strokeColor="#87d068"
                />
              </div>
              <div className={styles.nutrientItem}>
                <Text>碳水</Text>
                <Progress
                  percent={dietStats ? Math.round((dietStats.carbs / dietStats.carbsGoal) * 100) : 0}
                  format={() => `${dietStats?.carbs || 0}/${dietStats?.carbsGoal || 250}g`}
                  strokeColor="#ffd666"
                />
              </div>
              <div className={styles.nutrientItem}>
                <Text>脂肪</Text>
                <Progress
                  percent={dietStats ? Math.round((dietStats.fat / dietStats.fatGoal) * 100) : 0}
                  format={() => `${dietStats?.fat || 0}/${dietStats?.fatGoal || 65}g`}
                  strokeColor="#ff7875"
                />
              </div>
              <div className={styles.nutrientItem}>
                <Text>饮水</Text>
                <Progress
                  percent={dietStats ? Math.round((dietStats.water / dietStats.waterGoal) * 100) : 0}
                  format={() => `${dietStats?.water || 0}/${dietStats?.waterGoal || 2000}ml`}
                  strokeColor="#69c0ff"
                />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard