import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Button, Modal, Form, Input, InputNumber, Select, TimePicker, Table, Tag, Space, message, Progress } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { dietApi, type DietStats, DietMeal, RecommendedFood } from '../../services/diet'
import type { ColumnsType } from 'antd/es/table'

const mealTypes = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
]

const Diet: React.FC = () => {
  const [stats, setStats] = useState<DietStats | null>(null)
  const [meals, setMeals] = useState<DietMeal[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedFood[]>([])
  const [loading, setLoading] = useState(true)
  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<DietMeal | null>(null)
  const [addForm] = Form.useForm()
  const [editForm] = Form.useForm()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsData, mealsData, recs] = await Promise.all([
        dietApi.getTodayStats(),
        dietApi.getTodayMeals(),
        dietApi.getRecommendations(),
      ])
      setStats(statsData)
      setMeals(mealsData)
      setRecommendations(recs)
    } finally {
      setLoading(false)
    }
  }

  const handleAddMeal = async () => {
    try {
      const values = await addForm.validateFields()
      await dietApi.createMeal({
        ...values,
        calories: values.calories,
        protein: values.protein || 0,
        carbs: values.carbs || 0,
        fat: values.fat || 0,
        water: values.water || 0,
        time: values.time.format('HH:mm'),
      })
      message.success('添加成功')
      setAddOpen(false)
      addForm.resetFields()
      fetchData()
    } catch {
      message.error('添加失败')
    }
  }

  const handleEditMeal = async () => {
    if (!selectedMeal) return
    try {
      const values = await editForm.validateFields()
      await dietApi.updateMeal(selectedMeal.mealId, {
        mealName: values.mealName,
        calories: values.calories,
        protein: values.protein,
        carbs: values.carbs,
        fat: values.fat,
      })
      message.success('更新成功')
      setEditOpen(false)
      fetchData()
    } catch {
      message.error('更新失败')
    }
  }

  const handleDeleteMeal = async (mealId: number) => {
    try {
      await dietApi.deleteMeal(mealId)
      message.success('删除成功')
      fetchData()
    } catch {
      message.error('删除失败')
    }
  }

  const openEditDialog = (meal: DietMeal) => {
    setSelectedMeal(meal)
    editForm.setFieldsValue({
      mealName: meal.mealName,
      calories: meal.calories,
      protein: meal.protein,
      carbs: meal.carbs,
      fat: meal.fat,
    })
    setEditOpen(true)
  }

  const getProgressPercent = (current: number, goal: number) => {
    if (!goal) return 0
    return Math.round((current / goal) * 100)
  }

  const getMealTypeTag = (type: string) => {
    const colors: Record<string, string> = { breakfast: 'orange', lunch: 'green', dinner: 'blue', snack: 'purple' }
    const labels: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }
    return <Tag color={colors[type] || 'default'}>{labels[type] || type}</Tag>
  }

  const mealColumns: ColumnsType<DietMeal> = [
    { title: '类型', dataIndex: 'mealType', render: (v: string) => getMealTypeTag(v) },
    { title: '食物', dataIndex: 'mealName' },
    { title: '热量', dataIndex: 'calories', render: (v: number) => `${v} kcal` },
    { title: '蛋白质', dataIndex: 'protein', render: (v: number) => `${v}g` },
    { title: '碳水', dataIndex: 'carbs', render: (v: number) => `${v}g` },
    { title: '脂肪', dataIndex: 'fat', render: (v: number) => `${v}g` },
    { title: '时间', dataIndex: 'time' },
    {
      title: '操作',
      render: (_, record) => (
        <Space>
          <Button size="small" onClick={() => openEditDialog(record)}>编辑</Button>
          <Button size="small" danger onClick={() => handleDeleteMeal(record.mealId)}>删除</Button>
        </Space>
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>🍽️ 饮食管理</Typography.Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Typography.Text type="secondary">今日热量</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0', color: '#ff4d4f' }}>
              {loading ? '-' : `${stats?.calories || 0} / ${stats?.caloriesGoal || 2000} kcal`}
            </Typography.Title>
            <Progress
              percent={getProgressPercent(stats?.calories || 0, stats?.caloriesGoal || 2000)}
              strokeColor="#52c41a"
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>剩余 {stats?.remainingCalories || 0} kcal</Typography.Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Typography.Text type="secondary">连续记录</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0' }}>{loading ? '-' : `${stats?.streakDays || 0} 天`}</Typography.Title>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card>
            <Typography.Text type="secondary">饮水</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0' }}>{loading ? '-' : `${stats?.water || 0} / ${stats?.waterGoal || 2000} ml`}</Typography.Title>
            <Progress
              percent={getProgressPercent(stats?.water || 0, stats?.waterGoal || 2000)}
              strokeColor="#1890ff"
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: 24 }}>
        <Typography.Title level={5}>今日营养摄入</Typography.Title>
        <Row gutter={16} style={{ marginTop: 8 }}>
          <Col span={8}>
            <Typography.Text>蛋白质</Typography.Text>
            <Progress percent={getProgressPercent(stats?.protein || 0, stats?.proteinGoal || 150)} strokeColor="#52c41a" />
            <Typography.Text type="secondary">{stats?.protein || 0}/{stats?.proteinGoal || 150}g</Typography.Text>
          </Col>
          <Col span={8}>
            <Typography.Text>碳水</Typography.Text>
            <Progress percent={getProgressPercent(stats?.carbs || 0, stats?.carbsGoal || 250)} strokeColor="#faad14" />
            <Typography.Text type="secondary">{stats?.carbs || 0}/{stats?.carbsGoal || 250}g</Typography.Text>
          </Col>
          <Col span={8}>
            <Typography.Text>脂肪</Typography.Text>
            <Progress percent={getProgressPercent(stats?.fat || 0, stats?.fatGoal || 65)} strokeColor="#ff4d4f" />
            <Typography.Text type="secondary">{stats?.fat || 0}/{stats?.fatGoal || 65}g</Typography.Text>
          </Col>
        </Row>
      </Card>

      <Card style={{ marginTop: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>今日饮食记录</Typography.Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddOpen(true)}>添加记录</Button>
        </div>
        <Table
          columns={mealColumns}
          dataSource={meals}
          rowKey="mealId"
          size="small"
          pagination={false}
          loading={loading}
        />
      </Card>

      <Card style={{ marginTop: 24 }}>
        <Typography.Title level={5}>推荐食物</Typography.Title>
        <Row gutter={[16, 16]} style={{ marginTop: 8 }}>
          {recommendations.map(item => (
            <Col xs={24} sm={12} md={6} key={item.recommendId}>
              <Card size="small">
                <Typography.Text strong>{item.foodName}</Typography.Text>
                <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }}>{item.calories} kcal</Typography.Text>
                {item.protein && <Typography.Text type="secondary" style={{ fontSize: 12 }}>{item.protein}g蛋白质</Typography.Text>}
                {item.reason && <Tag color="blue" style={{ marginTop: 8 }}>{item.reason}</Tag>}
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      <Modal
        title="添加饮食记录"
        open={addOpen}
        onCancel={() => setAddOpen(false)}
        onOk={handleAddMeal}
        okText="提交"
        cancelText="取消"
      >
        <Form form={addForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="mealType" label="餐次类型" rules={[{ required: true }]}>
            <Select options={mealTypes} defaultValue="breakfast" />
          </Form.Item>
          <Form.Item name="mealName" label="食物名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="calories" label="热量" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} defaultValue={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="protein" label="蛋白质"><InputNumber style={{ width: '100%' }} defaultValue={0} /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}><Form.Item name="carbs" label="碳水"><InputNumber style={{ width: '100%' }} defaultValue={0} /></Form.Item></Col>
            <Col span={12}><Form.Item name="fat" label="脂肪"><InputNumber style={{ width: '100%' }} defaultValue={0} /></Form.Item></Col>
          </Row>
          <Form.Item name="water" label="饮水"><InputNumber style={{ width: '100%' }} defaultValue={0} /></Form.Item>
          <Form.Item name="time" label="时间" rules={[{ required: true }]}>
            <TimePicker style={{ width: '100%' }} defaultValue={dayjs()} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑饮食记录"
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={handleEditMeal}
        okText="更新"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="mealName" label="食物名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="calories" label="热量" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={8}><Form.Item name="protein" label="蛋白质"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="carbs" label="碳水"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="fat" label="脂肪"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default Diet
