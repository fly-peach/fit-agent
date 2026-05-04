import React, { useEffect, useState, useCallback } from 'react'
import { Card, Typography, Row, Col, Button, Modal, Form, Input, InputNumber, Select, TimePicker, DatePicker, Table, Tag, Space, message, Progress, AutoComplete, Divider, Radio, Checkbox, List, Avatar } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { Utensils, Sun, Moon, Sunrise, EditOutlined, DeleteOutlined } from 'lucide-react'
import dayjs from 'dayjs'
import { dietApi, type DietStats, DietMeal, type FoodItem } from '../../services/diet'
import type { ColumnsType } from 'antd/es/table'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'

const CALORIE_LEVEL_COLORS: Record<string, string> = {
  低: '#10B981',
  中: '#F59E0B',
  高: '#F59E0B',
  超高: '#EF4444',
}

const mealTypes = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
]

const MEAL_FILTERS = [
  { key: '', label: '全部', icon: null, color: '#666' },
  { key: 'breakfast', label: '早餐', icon: <Sunrise size={14} />, color: '#F59E0B' },
  { key: 'lunch', label: '午餐', icon: <Sun size={14} />, color: '#10B981' },
  { key: 'dinner', label: '晚餐', icon: <Moon size={14} />, color: '#6366F1' },
] as const

const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  return isMobile
}

const Diet: React.FC = () => {
  const [stats, setStats] = useState<DietStats | null>(null)
  const [meals, setMeals] = useState<DietMeal[]>([])
  const [loading, setLoading] = useState(true)
  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [customFoodOpen, setCustomFoodOpen] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<DietMeal | null>(null)
  const [addForm] = Form.useForm()
  const [editForm] = Form.useForm()
  const [customFoodForm] = Form.useForm()

  // Food autocomplete
  const [foodOptions, setFoodOptions] = useState<FoodItem[]>([])
  const [foodLoading, setFoodLoading] = useState(false)
  const [selectedFood, setSelectedFood] = useState<FoodItem | null>(null)
  const [foodCategories, setFoodCategories] = useState<string[]>([])
  const [mealFilter, setMealFilter] = useState('')
  const [currentSearch, setCurrentSearch] = useState('')

  // Diet trend chart
  const [trendDays, setTrendDays] = useState(7)
  const [trendLoading, setTrendLoading] = useState(false)
  const [trendData, setTrendData] = useState<any[]>([])
  const [trendGoals, setTrendGoals] = useState<{ caloriesGoal: number; proteinGoal: number; carbsGoal: number; fatGoal: number; waterGoal: number } | null>(null)
  const [activeMetrics, setActiveMetrics] = useState<string[]>(['calories'])
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [dayMeals, setDayMeals] = useState<DietMeal[]>([])
  const [dayMealsLoading, setDayMealsLoading] = useState(false)

  const isMobile = useIsMobile()

  useEffect(() => {
    fetchData()
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchTrendData()
  }, [trendDays])

  const fetchTrendData = async () => {
    setTrendLoading(true)
    try {
      const end = dayjs()
      const start = end.subtract(trendDays - 1, 'day')
      const result = await dietApi.getDateRangeTrend(start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'))
      const formatted = result.dailyStats.map(d => ({
        ...d,
        date: dayjs(d.date).format('MM/DD'),
        fullDate: d.date,
      }))
      setTrendData(formatted)
      setTrendGoals(result.goals)
    } catch {
      // ignore
    } finally {
      setTrendLoading(false)
    }
  }

  const fetchDayMeals = async (dateStr: string) => {
    setDayMealsLoading(true)
    try {
      const meals = await dietApi.getTodayMeals(dateStr)
      setDayMeals(meals)
      setSelectedDate(dateStr)
    } catch {
      setDayMeals([])
    } finally {
      setDayMealsLoading(false)
    }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsData, mealsData] = await Promise.all([
        dietApi.getTodayStats(),
        dietApi.getTodayMeals(),
      ])
      setStats(statsData)
      setMeals(mealsData)
    } finally {
      setLoading(false)
    }
  }

  const fetchCategories = async () => {
    try {
      const cats = await dietApi.getFoodCategories()
      setFoodCategories(cats)
    } catch {
      // ignore
    }
  }

  const doSearch = useCallback(async (keyword: string, mealType: string) => {
    setFoodLoading(true)
    try {
      const results = await dietApi.searchFoods(keyword || '', '', mealType)
      setFoodOptions(results)
    } catch {
      // ignore
    } finally {
      setFoodLoading(false)
    }
  }, [])

  const searchFoods = useCallback((keyword: string) => {
    setCurrentSearch(keyword)
    doSearch(keyword, mealFilter)
  }, [mealFilter, doSearch])

  const handleFoodSelect = (_value: string, food: FoodItem) => {
    setSelectedFood(food)
    addForm.setFieldsValue({
      mealName: food.name,
      calories: food.portionCalories,
      protein: food.protein,
      carbs: food.carbs,
      fat: food.fat,
    })
    if (food.suitableMeals) {
      const m = food.suitableMeals.split(',').filter((m: string) => m !== 'dinner')
      if (m.length > 0) {
        addForm.setFieldsValue({ mealType: m[0] })
      }
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
        mealDate: values.mealDate?.format('YYYY-MM-DD'),
      })
      message.success('添加成功')
      setAddOpen(false)
      addForm.resetFields()
      setSelectedFood(null)
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

  const [editFoodOptions, setEditFoodOptions] = useState<FoodItem[]>([])
  const [editFoodLoading, setEditFoodLoading] = useState(false)

  const searchEditFoods = useCallback(async (keyword: string) => {
    setEditFoodLoading(true)
    try {
      const results = await dietApi.searchFoods(keyword || '', '', '')
      setEditFoodOptions(results)
    } catch {
      // ignore
    } finally {
      setEditFoodLoading(false)
    }
  }, [])

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

  const handleAddCustomFood = async () => {
    try {
      const values = await customFoodForm.validateFields()
      await dietApi.addCustomFood({
        ...values,
        protein: values.protein || 0,
        carbs: values.carbs || 0,
        fat: values.fat || 0,
      })
      message.success('自定义食物已添加')
      setCustomFoodOpen(false)
      customFoodForm.resetFields()
      fetchCategories()
    } catch {
      message.error('添加失败')
    }
  }

  const getProgressPercent = (current: number, goal: number) => {
    if (!goal) return 0
    return Math.round((current / goal) * 100)
  }

  const getMealTypeTag = (type: string) => {
    const colors: Record<string, string> = { breakfast: '#F59E0B', lunch: '#10B981', dinner: '#0EA5E9', snack: '#8B5CF6' }
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
          <Button size="small" icon={<EditOutlined />} onClick={() => openEditDialog(record)} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteMeal(record.mealId)} />
        </Space>
      ),
    },
  ]

  return (
    <div className="fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#ECFEFF', color: '#06B6D4' }}>
          <Utensils size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>饮食管理</Typography.Title>
      </div>

      <Row gutter={[isMobile ? 12 : 16, isMobile ? 12 : 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%)' }}>
            <Typography.Text type="secondary">今日热量</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0', color: '#EF4444', fontWeight: 700 }}>
              {loading ? '-' : `${stats?.calories || 0} / ${stats?.caloriesGoal || 2000} kcal`}
            </Typography.Title>
            <Progress
              percent={getProgressPercent(stats?.calories || 0, stats?.caloriesGoal || 2000)}
              strokeColor="#10B981"
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>剩余 {stats?.remainingCalories || 0} kcal</Typography.Text>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card className="fitagent-card-hover" style={{ border: 'none' }}>
            <Typography.Text type="secondary">连续记录</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0 0', fontWeight: 700 }}>{loading ? '-' : `${stats?.streakDays || 0} 天`}</Typography.Title>
          </Card>
        </Col>
        <Col xs={24} sm={12} md={8}>
          <Card className="fitagent-card-hover" style={{ border: 'none', background: 'linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%)' }}>
            <Typography.Text type="secondary">饮水</Typography.Text>
            <Typography.Title level={3} style={{ margin: '8px 0', color: '#0EA5E9', fontWeight: 700 }}>{loading ? '-' : `${stats?.water || 0} / ${stats?.waterGoal || 2000} ml`}</Typography.Title>
            <Progress
              percent={getProgressPercent(stats?.water || 0, stats?.waterGoal || 2000)}
              strokeColor="#0EA5E9"
            />
          </Card>
        </Col>
      </Row>

      <Card style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <Typography.Title level={5}>今日营养摄入</Typography.Title>
        <Row gutter={isMobile ? 12 : 16} style={{ marginTop: 8 }}>
          <Col xs={24} sm={8}>
            <Typography.Text>蛋白质</Typography.Text>
            <Progress percent={getProgressPercent(stats?.protein || 0, stats?.proteinGoal || 150)} strokeColor="#10B981" />
            <Typography.Text type="secondary">{stats?.protein || 0}/{stats?.proteinGoal || 150}g</Typography.Text>
          </Col>
          <Col xs={24} sm={8}>
            <Typography.Text>碳水</Typography.Text>
            <Progress percent={getProgressPercent(stats?.carbs || 0, stats?.carbsGoal || 250)} strokeColor="#F59E0B" />
            <Typography.Text type="secondary">{stats?.carbs || 0}/{stats?.carbsGoal || 250}g</Typography.Text>
          </Col>
          <Col xs={24} sm={8}>
            <Typography.Text>脂肪</Typography.Text>
            <Progress percent={getProgressPercent(stats?.fat || 0, stats?.fatGoal || 65)} strokeColor="#EF4444" />
            <Typography.Text type="secondary">{stats?.fat || 0}/{stats?.fatGoal || 65}g</Typography.Text>
          </Col>
        </Row>
      </Card>

      {/* 饮食趋势图表 */}
      <Card style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>饮食趋势</Typography.Title>
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
            <Checkbox value="calories">热量</Checkbox>
            <Checkbox value="protein">蛋白质</Checkbox>
            <Checkbox value="carbs">碳水</Checkbox>
            <Checkbox value="fat">脂肪</Checkbox>
          </Space>
        </Checkbox.Group>

        <ResponsiveContainer width="100%" height={isMobile ? 220 : 300}>
          <LineChart data={trendLoading ? [] : trendData} onClick={(e: any) => {
            if (e?.activePayload?.[0]?.payload?.date) {
              const idx = trendData.findIndex(d => d.date === e.activePayload[0].payload.date)
              if (idx >= 0) {
                fetchDayMeals(trendData[idx].fullDate || trendData[idx].date)
              }
            }
          }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="date" tick={{ fontSize: isMobile ? 10 : 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: isMobile ? 10 : 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: isMobile ? 10 : 12 }} />
            <Tooltip
              formatter={(value: any, name: any) => {
                const labels: Record<string, string> = { calories: '热量', protein: '蛋白质', carbs: '碳水', fat: '脂肪', water: '饮水' }
                const units: Record<string, string> = { calories: ' kcal', protein: 'g', carbs: 'g', fat: 'g', water: 'ml' }
                return [`${value}${units[name] || ''}`, labels[name] || name]
              }}
            />
            {activeMetrics.includes('calories') && trendGoals && (
              <ReferenceLine yAxisId="left" y={trendGoals.caloriesGoal} stroke="#EF4444" strokeDasharray="4 4" label={{ value: '目标', fill: '#EF4444', fontSize: 10 }} />
            )}
            {activeMetrics.includes('calories') && <Line type="monotone" yAxisId="left" dataKey="calories" name="calories" stroke="#EF4444" strokeWidth={2} dot={{ r: 3 }} />}
            {activeMetrics.includes('protein') && trendGoals && (
              <ReferenceLine yAxisId="right" y={trendGoals.proteinGoal} stroke="#10B981" strokeDasharray="4 4" label={{ value: '目标', fill: '#10B981', fontSize: 10 }} />
            )}
            {activeMetrics.includes('protein') && <Line type="monotone" yAxisId="right" dataKey="protein" name="protein" stroke="#10B981" strokeWidth={2} dot={{ r: 3 }} />}
            {activeMetrics.includes('carbs') && trendGoals && (
              <ReferenceLine yAxisId="right" y={trendGoals.carbsGoal} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: '目标', fill: '#F59E0B', fontSize: 10 }} />
            )}
            {activeMetrics.includes('carbs') && <Line type="monotone" yAxisId="right" dataKey="carbs" name="carbs" stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />}
            {activeMetrics.includes('fat') && trendGoals && (
              <ReferenceLine yAxisId="right" y={trendGoals.fatGoal} stroke="#8B5CF6" strokeDasharray="4 4" label={{ value: '目标', fill: '#8B5CF6', fontSize: 10 }} />
            )}
            {activeMetrics.includes('fat') && <Line type="monotone" yAxisId="right" dataKey="fat" name="fat" stroke="#8B5CF6" strokeWidth={2} dot={{ r: 3 }} />}
          </LineChart>
        </ResponsiveContainer>

        {selectedDate && (
          <div style={{ marginTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <Typography.Text strong>{dayjs(selectedDate).format('YYYY-MM-DD')} 饮食记录</Typography.Text>
              <Button size="small" onClick={() => { setSelectedDate(null); setDayMeals([]) }}>关闭</Button>
            </div>
            {isMobile ? (
              <List
                dataSource={dayMeals}
                loading={dayMealsLoading}
                locale={{ emptyText: '暂无记录' }}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button size="small" icon={<EditOutlined />} onClick={() => { setSelectedDate(null); setDayMeals([]); openEditDialog(item) }} />,
                      <Button size="small" danger icon={<DeleteOutlined />} onClick={() => { handleDeleteMeal(item.mealId); fetchDayMeals(selectedDate) }} />,
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<Avatar style={{ backgroundColor: CALORIE_LEVEL_COLORS[item.mealType] || '#0EA5E9' }}>
                        {item.mealName.charAt(0)}
                      </Avatar>}
                      title={
                        <Space>
                          {getMealTypeTag(item.mealType)}
                          <span>{item.mealName}</span>
                        </Space>
                      }
                      description={`${item.calories} kcal · 蛋白质${item.protein}g · 碳水${item.carbs}g · 脂肪${item.fat}g · ${item.time}`}
                    />
                  </List.Item>
                )}
              />
            ) : (
              <Table
                columns={mealColumns}
                dataSource={dayMeals}
                rowKey="mealId"
                size="small"
                pagination={false}
                loading={dayMealsLoading}
                locale={{ emptyText: '暂无记录' }}
              />
            )}
          </div>
        )}
      </Card>

      <Card style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
          <Typography.Title level={5} style={{ margin: 0 }}>今日饮食记录</Typography.Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setAddOpen(true)}>添加记录</Button>
        </div>
        {isMobile ? (
          <List
            dataSource={meals}
            loading={loading}
            locale={{ emptyText: '暂无记录' }}
            renderItem={(item) => (
              <List.Item
                actions={[
                  <Button size="small" icon={<EditOutlined />} onClick={() => openEditDialog(item)} />,
                  <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteMeal(item.mealId)} />,
                ]}
              >
                <List.Item.Meta
                  avatar={<Avatar style={{ backgroundColor: CALORIE_LEVEL_COLORS[item.mealType] || '#0EA5E9' }}>
                    {item.mealName.charAt(0)}
                  </Avatar>}
                  title={
                    <Space>
                      {getMealTypeTag(item.mealType)}
                      <span>{item.mealName}</span>
                    </Space>
                  }
                  description={`${item.calories} kcal · 蛋白质${item.protein}g · 碳水${item.carbs}g · 脂肪${item.fat}g · ${item.time}`}
                />
              </List.Item>
            )}
          />
        ) : (
          <Table
            columns={mealColumns}
            dataSource={meals}
            rowKey="mealId"
            size="small"
            pagination={false}
            loading={loading}
          />
        )}
      </Card>

      {/* Add Meal Modal */}
      <Modal
        title="添加饮食记录"
        open={addOpen}
        onCancel={() => { setAddOpen(false); addForm.resetFields(); setSelectedFood(null); setMealFilter(''); setCurrentSearch(''); setFoodOptions([]) }}
        onOk={handleAddMeal}
        okText="提交"
        cancelText="取消"
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        <Form form={addForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ mealDate: dayjs() }}>
          <Form.Item name="mealType" label="餐次类型" rules={[{ required: true }]}>
            <Select options={mealTypes} defaultValue="breakfast" />
          </Form.Item>
          <Form.Item
            name="mealName"
            label={
              <span>食物名称 <Button size="small" type="link" style={{ padding: 0 }} onClick={() => setCustomFoodOpen(true)}>+ 添加新食物</Button></span>
            }
            rules={[{ required: true }]}
          >
            <AutoComplete
              placeholder="点击搜索食物，或直接输入食物名称..."
              notFoundContent={foodLoading ? '加载中...' : '未找到匹配的食物，可手动输入或添加新食物'}
              onSearch={searchFoods}
              onFocus={() => searchFoods('')}
              onSelect={(_value, option) => {
                const food = option.food as FoodItem
                if (food) handleFoodSelect(_value, food)
              }}
              dropdownRender={(menu) => (
                <div>
                  <div style={{ padding: '8px 12px', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {MEAL_FILTERS.map(m => (
                      <Button
                        key={m.key}
                        size="small"
                        type={mealFilter === m.key ? 'primary' : 'default'}
                        ghost={mealFilter === m.key}
                        icon={m.icon}
                        onClick={() => {
                          setMealFilter(m.key)
                          doSearch(currentSearch, m.key)
                        }}
                      >
                        {m.label}
                      </Button>
                    ))}
                  </div>
                  <Divider style={{ margin: 0 }} />
                  {menu}
                </div>
              )}
              options={foodOptions.map(food => ({
                value: food.name,
                label: (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>
                      <strong>{food.name}</strong>
                      {food.portionUnit && <span style={{ color: '#999', fontSize: 12, marginLeft: 6 }}>{food.portionUnit}</span>}
                    </span>
                    <span style={{ color: '#EF4444', fontSize: 12 }}>{food.portionCalories} kcal</span>
                  </div>
                ),
                food,
              }))}
            />
          </Form.Item>

          {selectedFood && (
            <div style={{ marginBottom: 16, padding: 10, background: '#F0FDF4', borderRadius: 8 }}>
              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                {selectedFood.name} · {selectedFood.portionCalories} kcal/份
                {selectedFood.protein > 0 && ` · 蛋白质${selectedFood.protein}g`}
                {selectedFood.carbs > 0 && ` · 碳水${selectedFood.carbs}g`}
                {selectedFood.fat > 0 && ` · 脂肪${selectedFood.fat}g`}
                {selectedFood.calorieLevel && (
                  <Tag color={CALORIE_LEVEL_COLORS[selectedFood.calorieLevel]} style={{ marginLeft: 8 }}>
                    {selectedFood.calorieLevel}热量
                  </Tag>
                )}
              </Typography.Text>
            </div>
          )}

          <Row gutter={16}>
            <Col xs={12}><Form.Item name="calories" label="热量" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} defaultValue={0} addonAfter="kcal" /></Form.Item></Col>
            <Col xs={12}><Form.Item name="protein" label="蛋白质"><InputNumber style={{ width: '100%' }} defaultValue={0} addonAfter="g" /></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col xs={12}><Form.Item name="carbs" label="碳水"><InputNumber style={{ width: '100%' }} defaultValue={0} addonAfter="g" /></Form.Item></Col>
            <Col xs={12}><Form.Item name="fat" label="脂肪"><InputNumber style={{ width: '100%' }} defaultValue={0} addonAfter="g" /></Form.Item></Col>
          </Row>
          <Form.Item name="water" label="饮水"><InputNumber style={{ width: '100%' }} defaultValue={0} addonAfter="ml" /></Form.Item>
          <Form.Item name="mealDate" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="time" label="时间" rules={[{ required: true }]}>
            <TimePicker style={{ width: '100%' }} defaultValue={dayjs()} />
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        title="编辑饮食记录"
        open={editOpen}
        onCancel={() => { setEditOpen(false); setEditFoodOptions([]); setEditFoodLoading(false) }}
        onOk={handleEditMeal}
        okText="更新"
        cancelText="取消"
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        <Form form={editForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="mealName" label="食物名称" rules={[{ required: true }]}>
            <AutoComplete
              placeholder="搜索食物..."
              notFoundContent={editFoodLoading ? '加载中...' : '未找到匹配的食物'}
              onSearch={searchEditFoods}
              onSelect={(_value, option) => {
                const food = option.food as FoodItem
                if (food) {
                  editForm.setFieldsValue({
                    mealName: food.name,
                    calories: food.portionCalories,
                    protein: food.protein,
                    carbs: food.carbs,
                    fat: food.fat,
                  })
                }
              }}
              options={editFoodOptions.map(food => ({
                value: food.name,
                label: (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span><strong>{food.name}</strong>{food.portionUnit && <span style={{ color: '#999', fontSize: 12, marginLeft: 6 }}>{food.portionUnit}</span>}</span>
                    <span style={{ color: '#EF4444', fontSize: 12 }}>{food.portionCalories} kcal</span>
                  </div>
                ),
                food,
              }))}
            />
          </Form.Item>
          <Form.Item name="calories" label="热量" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={8}><Form.Item name="protein" label="蛋白质"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={8}><Form.Item name="carbs" label="碳水"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
            <Col xs={8}><Form.Item name="fat" label="脂肪"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>

      {/* Custom Food Modal */}
      <Modal
        title="添加自定义食物"
        open={customFoodOpen}
        onCancel={() => { setCustomFoodOpen(false); customFoodForm.resetFields() }}
        onOk={handleAddCustomFood}
        okText="添加"
        cancelText="取消"
        width={isMobile ? '100%' : undefined}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        <Form form={customFoodForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="name" label="食物名称" rules={[{ required: true }]}>
            <Input placeholder="如：自制燕麦饼干" />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Select placeholder="选择分类" options={foodCategories.map(c => ({ label: c, value: c }))} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={12}><Form.Item name="portionUnit" label="一份单位"><Input placeholder="如：1 块" /></Form.Item></Col>
            <Col xs={12}><Form.Item name="portionGrams" label="一份克数"><InputNumber style={{ width: '100%' }} addonAfter="g" /></Form.Item></Col>
          </Row>
          <Form.Item name="portionCalories" label="一份热量" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} addonAfter="kcal" />
          </Form.Item>
          <Form.Item name="caloriesPer100g" label="每100g热量" rules={[{ required: true }]}>
            <InputNumber style={{ width: '100%' }} addonAfter="kcal" />
          </Form.Item>
          <Form.Item name="calorieLevel" label="热量等级">
            <Select options={[
              { label: '低', value: '低' },
              { label: '中', value: '中' },
              { label: '高', value: '高' },
              { label: '超高', value: '超高' },
            ]} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={8}><Form.Item name="protein" label="蛋白质"><InputNumber style={{ width: '100%' }} addonAfter="g" defaultValue={0} /></Form.Item></Col>
            <Col xs={8}><Form.Item name="carbs" label="碳水"><InputNumber style={{ width: '100%' }} addonAfter="g" defaultValue={0} /></Form.Item></Col>
            <Col xs={8}><Form.Item name="fat" label="脂肪"><InputNumber style={{ width: '100%' }} addonAfter="g" defaultValue={0} /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default Diet