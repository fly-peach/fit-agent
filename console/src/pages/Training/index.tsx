import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Button, Modal, Form, Input, InputNumber, Select, DatePicker, Progress, Avatar, List, Tag, Space, message, Radio, Checkbox } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { Dumbbell } from 'lucide-react'
import dayjs from 'dayjs'
import { trainingApi, type WeeklyStats, TrainingSchedule, RecommendedTraining } from '../../services/training'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const planTypes = [
  { value: 'strength', label: '力量训练' },
  { value: 'cardio', label: '有氧运动' },
  { value: 'flexibility', label: '柔韧训练' },
]

const intensities = [
  { value: 'low', label: '低强度' },
  { value: 'medium', label: '中等强度' },
  { value: 'high', label: '高强度' },
]

const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const Training: React.FC = () => {
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedTraining[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)
  const [createForm] = Form.useForm()
  const [completeForm] = Form.useForm()

  // Training trend chart
  const [trendDays, setTrendDays] = useState(7)
  const [trendLoading, setTrendLoading] = useState(false)
  const [trendData, setTrendData] = useState<any[]>([])
  const [activeMetrics, setActiveMetrics] = useState<string[]>(['duration', 'caloriesBurned'])

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    fetchTrendData()
  }, [trendDays])

  const fetchTrendData = async () => {
    setTrendLoading(true)
    try {
      const end = dayjs()
      const start = end.subtract(trendDays - 1, 'day')
      const result = await trainingApi.getDateRangeTrend(start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'))
      const formatted = result.dailyStats.map(d => ({
        ...d,
        date: dayjs(d.date).format('MM/DD'),
      }))
      setTrendData(formatted)
    } catch {
      // ignore
    } finally {
      setTrendLoading(false)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const [stats, sched, recs] = await Promise.all([
        trainingApi.getWeeklyStats(),
        trainingApi.getWeeklySchedule(),
        trainingApi.getRecommendations(),
      ])
      setWeeklyStats(stats)
      setSchedule(sched)
      setRecommendations(recs)
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePlan = async () => {
    try {
      const values = await createForm.validateFields()
      await trainingApi.createPlan({
        ...values,
        estimatedDuration: values.estimatedDuration,
        scheduledDate: values.scheduledDate.format('YYYY-MM-DD'),
      })
      message.success('创建成功')
      setCreateOpen(false)
      createForm.resetFields()
      fetchData()
    } catch {
      message.error('创建失败')
    }
  }

  const handleCompletePlan = async () => {
    if (!selectedPlanId) return
    try {
      const values = await completeForm.validateFields()
      await trainingApi.completePlan(selectedPlanId, {
        ...values,
        completedDate: values.completedDate?.format('YYYY-MM-DD'),
      })
      message.success('完成记录成功')
      setCompleteOpen(false)
      completeForm.resetFields()
      fetchData()
    } catch {
      message.error('记录失败')
    }
  }

  const handleDeletePlan = async (planId: number) => {
    try {
      await trainingApi.deletePlan(planId)
      message.success('删除成功')
      fetchData()
    } catch {
      message.error('删除失败')
    }
  }

  const getProgressPercent = () => {
    if (!weeklyStats || weeklyStats.weeklyCount === 0) return 0
    return Math.round((weeklyStats.completedCount / weeklyStats.weeklyCount) * 100)
  }

  const getTypeTag = (type: string) => {
    const colors: Record<string, string> = { strength: '#F59E0B', cardio: '#10B981', flexibility: '#0EA5E9' }
    const labels: Record<string, string> = { strength: '力量', cardio: '有氧', flexibility: '柔韧' }
    return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>
  }

  const getIntensityTag = (intensity: string) => {
    const colors: Record<string, string> = { low: '#06B6D4', medium: '#F59E0B', high: '#EF4444' }
    return <Tag color={colors[intensity] || 'default'}>{intensity}</Tag>
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#FFF7ED', color: '#F59E0B' }}>
          <Dumbbell size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>训练计划</Typography.Title>
      </div>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%)' }}>
            <Typography.Text type="secondary">本周训练</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#10B981', fontWeight: 700 }}>{loading ? '-' : `${weeklyStats?.weeklyCount || 0} 次`}</Typography.Title>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none' }}>
            <Typography.Text type="secondary">本周时长</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0', fontWeight: 700 }}>{loading ? '-' : `${weeklyStats?.weeklyHours || 0} 小时`}</Typography.Title>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%)' }}>
            <Typography.Text type="secondary">消耗热量</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#F59E0B', fontWeight: 700 }}>{loading ? '-' : `${weeklyStats?.weeklyCalories || 0} kcal`}</Typography.Title>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%)' }}>
            <Typography.Text type="secondary">连续训练</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0', color: '#8B5CF6', fontWeight: 700 }}>{loading ? '-' : `${weeklyStats?.streakDays || 0} 天`}</Typography.Title>
          </Card>
        </Col>
      </Row>

      {/* 训练趋势图表 */}
      <Card style={{ marginTop: 24, border: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>训练趋势</Typography.Title>
          <Radio.Group value={trendDays} onChange={e => setTrendDays(e.target.value)} size="small">
            <Radio.Button value={7}>近7天</Radio.Button>
            <Radio.Button value={14}>近14天</Radio.Button>
            <Radio.Button value={30}>近30天</Radio.Button>
          </Radio.Group>
        </div>

        <Checkbox.Group
          value={activeMetrics}
          onChange={(vals: any[]) => setActiveMetrics(vals)}
          style={{ marginBottom: 16 }}
        >
          <Space wrap>
            <Checkbox value="duration">时长</Checkbox>
            <Checkbox value="caloriesBurned">消耗热量</Checkbox>
          </Space>
        </Checkbox.Group>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={trendLoading ? [] : trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} />
            <Tooltip
              formatter={(value: any, name: any) => {
                const labels: Record<string, string> = { duration: '时长', caloriesBurned: '消耗热量', planCount: '计划数' }
                const units: Record<string, string> = { duration: ' 分钟', caloriesBurned: ' kcal' }
                return [`${value}${units[name] || ''}`, labels[name] || name]
              }}
            />
            {activeMetrics.includes('duration') && <Line type="monotone" yAxisId="left" dataKey="duration" name="duration" stroke="#10B981" strokeWidth={2} dot={{ r: 3 }} />}
            {activeMetrics.includes('caloriesBurned') && <Line type="monotone" yAxisId="right" dataKey="caloriesBurned" name="caloriesBurned" stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />}
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card style={{ marginTop: 24, border: 'none' }}>
        <Typography.Title level={5}>本周进度</Typography.Title>
        <Progress percent={getProgressPercent()} strokeColor="#10B981" />
        <Space style={{ marginTop: 16 }}>
          {weekDays.map((day, idx) => {
            const daySchedule = schedule.filter(s => s.dayOfWeek === idx + 1)
            const completed = daySchedule.some(s => s.status === 'completed')
            return (
              <div key={day} style={{ textAlign: 'center' }}>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>{day}</Typography.Text>
                <br />
                <Avatar style={{ backgroundColor: completed ? '#10B981' : '#d9d9d9', marginTop: 8 }}>
                  {completed ? '✓' : idx + 1}
                </Avatar>
              </div>
            )
          })}
        </Space>
      </Card>

      <Card style={{ marginTop: 24, border: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>本周训练安排</Typography.Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>新建计划</Button>
        </div>
        <List
          itemLayout="horizontal"
          dataSource={schedule}
          renderItem={(item) => (
            <List.Item
              actions={item.status === 'completed' ? [] : [
                <Button size="small" type="primary" onClick={() => { setSelectedPlanId(item.planId || 0); setCompleteOpen(true) }}>完成</Button>,
                <Button size="small" danger onClick={() => handleDeletePlan(item.planId || 0)}>删除</Button>,
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Avatar style={{ backgroundColor: item.status === 'completed' ? '#10B981' : '#0EA5E9' }}>
                    {item.status === 'completed' ? '✓' : item.dayOfWeek}
                  </Avatar>
                }
                title={item.planName}
                description={`${item.duration}分钟 · ${item.intensity}强度`}
              />
              <Space>
                {getTypeTag(item.planType)}
                {getIntensityTag(item.intensity)}
                <Tag color={item.status === 'completed' ? '#10B981' : '#06B6D4'}>
                  {item.status === 'completed' ? '已完成' : '待完成'}
                </Tag>
              </Space>
            </List.Item>
          )}
        />
      </Card>

      <Card style={{ marginTop: 24, border: 'none' }}>
        <Typography.Title level={5}>推荐训练</Typography.Title>
        <Row gutter={[16, 16]} style={{ marginTop: 8 }}>
          {recommendations.map(item => (
            <Col xs={24} sm={12} md={6} key={item.recommendId}>
              <Card size="small" className="fitagent-card-hover" style={{ border: 'none' }}>
                <Typography.Text strong>{item.planName}</Typography.Text>
                <div style={{ marginTop: 8 }}>
                  <Space>
                    {getTypeTag(item.planType)}
                    {getIntensityTag(item.intensity)}
                  </Space>
                </div>
                <Typography.Text type="secondary" style={{ fontSize: 12 }}>{item.duration}分钟</Typography.Text>
                {item.caloriesBurn && (
                  <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                    消耗 {item.caloriesBurn} kcal
                  </Typography.Text>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <Modal
        title="创建训练计划"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        onOk={handleCreatePlan}
        okText="创建"
        cancelText="取消"
      >
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="planName" label="计划名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="planType" label="训练类型" rules={[{ required: true }]}>
            <Select options={planTypes} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="targetIntensity" label="目标强度" rules={[{ required: true }]}>
                <Select options={intensities} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="estimatedDuration" label="预计时长" rules={[{ required: true }]}>
                <InputNumber addonAfter="分钟" style={{ width: '100%' }} defaultValue={60} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="scheduledDate" label="计划日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} defaultValue={dayjs()} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="完成训练"
        open={completeOpen}
        onCancel={() => setCompleteOpen(false)}
        onOk={handleCompletePlan}
        okText="提交"
        cancelText="取消"
      >
        <Form form={completeForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ completedDate: dayjs() }}>
          <Form.Item name="completedDate" label="完成日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="actualDuration" label="实际时长" rules={[{ required: true }]}>
            <InputNumber addonAfter="分钟" style={{ width: '100%' }} defaultValue={60} />
          </Form.Item>
          <Form.Item name="actualIntensity" label="实际强度" rules={[{ required: true }]}>
            <Select options={intensities} />
          </Form.Item>
          <Form.Item name="caloriesBurned" label="消耗热量">
            <InputNumber addonAfter="kcal" style={{ width: '100%' }} defaultValue={0} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Training
