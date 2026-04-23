import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  TimePicker,
  Select,
  message,
  Typography,
  Space,
  List,
} from 'antd'
import {
  ThunderboltOutlined,
  CoffeeOutlined,
  PlusOutlined,
  DeleteOutlined,
  EditOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import { dietApi, type DietStats, DietMeal, RecommendedFood } from '../../services/diet'
import styles from './Diet.module.css'

const { Title, Text } = Typography

const mealTypes = [
  { value: 'breakfast', label: '早餐', color: 'orange' },
  { value: 'lunch', label: '午餐', color: 'green' },
  { value: 'dinner', label: '晚餐', color: 'blue' },
  { value: 'snack', label: '加餐', color: 'purple' },
]

const Diet: React.FC = () => {
  const [stats, setStats] = useState<DietStats | null>(null)
  const [meals, setMeals] = useState<DietMeal[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedFood[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [editModalVisible, setEditModalVisible] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<DietMeal | null>(null)
  const [form] = Form.useForm()
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

  const handleAddMeal = async (values: {
    mealType: string
    mealName: string
    calories: number
    protein: number
    carbs: number
    fat: number
    water: number
    time: dayjs.Dayjs
    note: string
  }) => {
    try {
      await dietApi.createMeal({
        ...values,
        time: values.time.format('HH:mm'),
      })
      message.success('添加成功')
      setModalVisible(false)
      form.resetFields()
      fetchData()
    } catch {
      message.error('添加失败')
    }
  }

  const handleEditMeal = async (values: Partial<DietMeal>) => {
    if (!selectedMeal) return
    try {
      await dietApi.updateMeal(selectedMeal.mealId, values)
      message.success('更新成功')
      setEditModalVisible(false)
      editForm.resetFields()
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

  const getMealTypeTag = (type: string) => {
    const found = mealTypes.find((m) => m.value === type)
    return <Tag color={found?.color || 'default'}>{found?.label || type}</Tag>
  }

  const columns: ColumnsType<DietMeal> = [
    {
      title: '类型',
      dataIndex: 'mealType',
      key: 'mealType',
      render: getMealTypeTag,
    },
    {
      title: '食物',
      dataIndex: 'mealName',
      key: 'mealName',
    },
    {
      title: '热量',
      dataIndex: 'calories',
      key: 'calories',
      render: (val: number) => `${val} kcal`,
    },
    {
      title: '蛋白质',
      dataIndex: 'protein',
      key: 'protein',
      render: (val: number) => `${val}g`,
    },
    {
      title: '碳水',
      dataIndex: 'carbs',
      key: 'carbs',
      render: (val: number) => `${val}g`,
    },
    {
      title: '脂肪',
      dataIndex: 'fat',
      key: 'fat',
      render: (val: number) => `${val}g`,
    },
    {
      title: '时间',
      dataIndex: 'time',
      key: 'time',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button
            size="small"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedMeal(record)
              editForm.setFieldsValue(record)
              setEditModalVisible(true)
            }}
          />
          <Button
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteMeal(record.mealId)}
          />
        </Space>
      ),
    },
  ]

  return (
    <div className={styles.container}>
      <Title level={3}>
        <CoffeeOutlined /> 饮食管理
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card loading={loading}>
            <Statistic
              title="今日热量"
              value={stats?.calories || 0}
              suffix={`/ ${stats?.caloriesGoal || 2000} kcal`}
              prefix={<ThunderboltOutlined />}
            />
            <Progress
              percent={
                stats ? Math.round((stats.calories / stats.caloriesGoal) * 100) : 0
              }
              strokeColor={{
                '0%': '#87d068',
                '100%': '#52c41a',
              }}
            />
            <Text type="secondary">剩余 {stats?.remainingCalories || 0} kcal</Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card loading={loading}>
            <Statistic title="连续记录" value={stats?.streakDays || 0} suffix="天" />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card loading={loading}>
            <Statistic title="饮水" value={stats?.water || 0} suffix={`/ ${stats?.waterGoal || 2000}ml`} />
            <Progress
              percent={
                stats ? Math.round((stats.water / stats.waterGoal) * 100) : 0
              }
              strokeColor="#69c0ff"
            />
          </Card>
        </Col>
      </Row>

      <Card title="今日营养摄入" loading={loading} style={{ marginTop: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div className={styles.nutrient}>
              <Text>蛋白质</Text>
              <Progress
                percent={
                  stats ? Math.round((stats.protein / stats.proteinGoal) * 100) : 0
                }
                format={() => `${stats?.protein || 0}/${stats?.proteinGoal || 150}g`}
                strokeColor="#87d068"
              />
            </div>
          </Col>
          <Col span={8}>
            <div className={styles.nutrient}>
              <Text>碳水</Text>
              <Progress
                percent={
                  stats ? Math.round((stats.carbs / stats.carbsGoal) * 100) : 0
                }
                format={() => `${stats?.carbs || 0}/${stats?.carbsGoal || 250}g`}
                strokeColor="#ffd666"
              />
            </div>
          </Col>
          <Col span={8}>
            <div className={styles.nutrient}>
              <Text>脂肪</Text>
              <Progress
                percent={
                  stats ? Math.round((stats.fat / stats.fatGoal) * 100) : 0
                }
                format={() => `${stats?.fat || 0}/${stats?.fatGoal || 65}g`}
                strokeColor="#ff7875"
              />
            </div>
          </Col>
        </Row>
      </Card>

      <Card
        title="今日饮食记录"
        loading={loading}
        style={{ marginTop: 16 }}
        extra={
          <Button icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            添加记录
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={meals}
          rowKey="mealId"
          pagination={false}
        />
      </Card>

      <Card title="推荐食物" loading={loading} style={{ marginTop: 16 }}>
        <List
          grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 4 }}
          dataSource={recommendations}
          renderItem={(item) => (
            <List.Item>
              <Card hoverable size="small">
                <Title level={5}>{item.foodName}</Title>
                <Text>{item.calories} kcal</Text>
                {item.protein && <Text type="secondary"> · {item.protein}g蛋白质</Text>}
                {item.reason && (
                  <div style={{ marginTop: 8 }}>
                    <Tag color="blue">{item.reason}</Tag>
                  </div>
                )}
              </Card>
            </List.Item>
          )}
        />
      </Card>

      <Modal
        title="添加饮食记录"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} onFinish={handleAddMeal} layout="vertical">
          <Form.Item name="mealType" label="餐次类型" rules={[{ required: true }]}>
            <Select options={mealTypes.map((m) => ({ value: m.value, label: m.label }))} />
          </Form.Item>
          <Form.Item name="mealName" label="食物名称" rules={[{ required: true }]}>
            <Input placeholder="如：鸡胸肉沙拉" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="calories" label="热量" rules={[{ required: true }]}>
                <InputNumber min={0} max={2000} addonAfter="kcal" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="protein" label="蛋白质" initialValue={0}>
                <InputNumber min={0} max={100} addonAfter="g" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="carbs" label="碳水" initialValue={0}>
                <InputNumber min={0} max={200} addonAfter="g" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="fat" label="脂肪" initialValue={0}>
                <InputNumber min={0} max={50} addonAfter="g" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="water" label="饮水" initialValue={0}>
            <InputNumber min={0} max={500} addonAfter="ml" />
          </Form.Item>
          <Form.Item name="time" label="时间" rules={[{ required: true }]}>
            <TimePicker format="HH:mm" />
          </Form.Item>
          <Form.Item name="note" label="备注">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              提交
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="编辑饮食记录"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        footer={null}
      >
        <Form form={editForm} onFinish={handleEditMeal} layout="vertical">
          <Form.Item name="mealName" label="食物名称">
            <Input />
          </Form.Item>
          <Form.Item name="calories" label="热量">
            <InputNumber min={0} max={2000} addonAfter="kcal" />
          </Form.Item>
          <Form.Item name="protein" label="蛋白质">
            <InputNumber min={0} max={100} addonAfter="g" />
          </Form.Item>
          <Form.Item name="carbs" label="碳水">
            <InputNumber min={0} max={200} addonAfter="g" />
          </Form.Item>
          <Form.Item name="fat" label="脂肪">
            <InputNumber min={0} max={50} addonAfter="g" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>
              更新
            </Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Diet