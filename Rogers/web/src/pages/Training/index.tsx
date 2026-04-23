import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  List,
  Tag,
  Avatar,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  DatePicker,
  Select,
  message,
  Typography,
  Space,
} from 'antd'
import {
  FireOutlined,
  TrophyOutlined,
  PlusOutlined,
  CheckOutlined,
  DeleteOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { trainingApi, type WeeklyStats, TrainingSchedule, RecommendedTraining, TrainingPlan } from '../../services/training'
import styles from './Training.module.css'

const { Title, Text } = Typography

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

const Training: React.FC = () => {
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedTraining[]>([])
  const [loading, setLoading] = useState(true)
  const [createModalVisible, setCreateModalVisible] = useState(false)
  const [completeModalVisible, setCompleteModalVisible] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)
  const [createForm] = Form.useForm()
  const [completeForm] = Form.useForm()

  useEffect(() => {
    fetchData()
  }, [])

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

  const handleCreatePlan = async (values: TrainingPlan) => {
    try {
      await trainingApi.createPlan({
        ...values,
        scheduledDate: dayjs(values.scheduledDate).format('YYYY-MM-DD'),
      })
      message.success('创建成功')
      setCreateModalVisible(false)
      createForm.resetFields()
      fetchData()
    } catch {
      message.error('创建失败')
    }
  }

  const handleCompletePlan = async (values: { actualDuration: number; actualIntensity: string; caloriesBurned: number }) => {
    if (!selectedPlanId) return
    try {
      await trainingApi.completePlan(selectedPlanId, values)
      message.success('完成记录成功')
      setCompleteModalVisible(false)
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

  const getIntensityTag = (intensity: string) => {
    switch (intensity) {
      case 'low':
        return <Tag color="blue">低</Tag>
      case 'medium':
        return <Tag color="orange">中</Tag>
      case 'high':
        return <Tag color="red">高</Tag>
      default:
        return <Tag>{intensity}</Tag>
    }
  }

  const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

  return (
    <div className={styles.container}>
      <Title level={3}>
        <FireOutlined /> 训练计划
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
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="本周时长"
              value={weeklyStats?.weeklyHours || 0}
              suffix="小时"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card loading={loading}>
            <Statistic
              title="消耗热量"
              value={weeklyStats?.weeklyCalories || 0}
              suffix="kcal"
            />
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
          </Card>
        </Col>
      </Row>

      <Card
        title="本周进度"
        loading={loading}
        style={{ marginTop: 16 }}
      >
        <Progress
          percent={
            weeklyStats && weeklyStats.weeklyCount > 0
              ? Math.round((weeklyStats.completedCount / weeklyStats.weeklyCount) * 100)
              : 0
          }
          format={(percent) => `已完成 ${percent}%`}
        />
        <Row gutter={8} style={{ marginTop: 16 }}>
          {weekDays.map((day, idx) => {
            const daySchedule = schedule.filter((s) => s.dayOfWeek === idx + 1)
            const completed = daySchedule.some((s) => s.status === 'completed')
            return (
              <Col key={day} span={3}>
                <div className={styles.dayBox}>
                  <Text>{day}</Text>
                  <Avatar
                    size={32}
                    style={{ backgroundColor: completed ? '#52c41a' : '#f0f0f0' }}
                  >
                    {completed ? <CheckOutlined /> : idx + 1}
                  </Avatar>
                </div>
              </Col>
            )
          })}
        </Row>
      </Card>

      <Card
        title="本周训练安排"
        loading={loading}
        style={{ marginTop: 16 }}
        extra={
          <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
            新建计划
          </Button>
        }
      >
        <List
          dataSource={schedule}
          renderItem={(item) => (
            <List.Item
              actions={
                item.status === 'pending'
                  ? [
                      <Button
                        type="primary"
                        size="small"
                        onClick={() => {
                          setSelectedPlanId(item.planId || 0)
                          setCompleteModalVisible(true)
                        }}
                      >
                        完成
                      </Button>,
                      <Button
                        danger
                        size="small"
                        icon={<DeleteOutlined />}
                        onClick={() => handleDeletePlan(item.planId || 0)}
                      />,
                    ]
                  : undefined
              }
            >
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
                title={`${item.planName} - ${dayjs(item.date).format('MM-DD')}`}
                description={
                  <Space>
                    {getPlanTypeTag(item.planType)}
                    {getIntensityTag(item.intensity)}
                    <Text type="secondary">{item.duration}分钟</Text>
                  </Space>
                }
              />
              <Tag color={item.status === 'completed' ? 'green' : 'blue'}>
                {item.status === 'completed' ? '已完成' : '待完成'}
              </Tag>
            </List.Item>
          )}
        />
      </Card>

      <Card title="推荐训练" loading={loading} style={{ marginTop: 16 }}>
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
          dataSource={recommendations}
          renderItem={(item) => (
            <List.Item>
              <Card hoverable>
                <Title level={5}>{item.planName}</Title>
                <Space direction="vertical" size="small">
                  {getPlanTypeTag(item.planType)}
                  {getIntensityTag(item.intensity)}
                  <Text type="secondary">{item.duration}分钟</Text>
                  {item.caloriesBurn && (
                    <Text type="secondary">消耗 {item.caloriesBurn} kcal</Text>
                  )}
                </Space>
              </Card>
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="创建训练计划"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        footer={null}
      >
        <Form form={createForm} onFinish={handleCreatePlan} layout="vertical">
          <Form.Item name="planName" label="计划名称" rules={[{ required: true }]}>
            <Input placeholder="如：力量训练-上肢" />
          </Form.Item>
          <Form.Item name="planType" label="训练类型" rules={[{ required: true }]}>
            <Select options={planTypes} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="targetIntensity" label="目标强度" initialValue="medium">
                <Select options={intensities} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="estimatedDuration" label="预计时长" initialValue={60}>
                <InputNumber min={10} max={180} addonAfter="分钟" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="scheduledDate" label="计划日期" rules={[{ required: true }]}>
            <DatePicker />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              创建
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="完成训练"
        open={completeModalVisible}
        onCancel={() => setCompleteModalVisible(false)}
        footer={null}
      >
        <Form form={completeForm} onFinish={handleCompletePlan} layout="vertical">
          <Form.Item name="actualDuration" label="实际时长" rules={[{ required: true }]}>
            <InputNumber min={10} max={180} addonAfter="分钟" />
          </Form.Item>
          <Form.Item name="actualIntensity" label="实际强度" initialValue="medium">
            <Select options={intensities} />
          </Form.Item>
          <Form.Item name="caloriesBurned" label="消耗热量">
            <InputNumber min={0} max={1000} addonAfter="kcal" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Training