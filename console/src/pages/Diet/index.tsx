import React, { useEffect, useState, useCallback } from 'react'
import { App, Card, Typography, Row, Col, Button, Modal, Form, Input, InputNumber, Select, TimePicker, DatePicker, Table, Tag, Space, Progress, AutoComplete, Divider, Radio, Checkbox, List, Avatar, Calendar } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { Utensils, Sun, Moon, Sunrise } from 'lucide-react'
import dayjs from 'dayjs'
import { dietApi, type DietStats, DietMeal, type FoodItem } from '../../services/diet'
import type { ColumnsType } from 'antd/es/table'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useIsMobile } from '../../hooks'

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

const METRIC_STYLES: Record<string, { label: string; color: string; unit: string }> = {
  calories: { label: '热量', color: '#ef4444', unit: ' kcal' },
  protein: { label: '蛋白质', color: '#10b981', unit: 'g' },
  carbs: { label: '碳水', color: '#f59e0b', unit: 'g' },
  fat: { label: '脂肪', color: '#8b5cf6', unit: 'g' },
}

const Diet: React.FC = () => {
  const { message } = App.useApp()
  const sharedTrendLineMotion = {
    isAnimationActive: true,
    animationBegin: 0,
    animationDuration: 420,
    animationEasing: 'ease-out' as const,
  }
  const [stats, setStats] = useState<DietStats | null>(null)
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
  const [activeMetrics, setActiveMetrics] = useState<string[]>(['calories'])
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const [dayMeals, setDayMeals] = useState<DietMeal[]>([])
  const [dayMealsLoading, setDayMealsLoading] = useState(false)
  const [currentMonth, setCurrentMonth] = useState(dayjs())
  const [calendarStatsMap, setCalendarStatsMap] = useState<Record<string, {
    calories: number
    protein: number
    carbs: number
    fat: number
    water: number
    mealCount: number
  }>>({})
  const [calendarLoading, setCalendarLoading] = useState(false)
  const [selectedCalendarDate, setSelectedCalendarDate] = useState<string>(dayjs().format('YYYY-MM-DD'))
  const [selectedCalendarMeals, setSelectedCalendarMeals] = useState<DietMeal[]>([])
  const [selectedCalendarMealsLoading, setSelectedCalendarMealsLoading] = useState(false)

  const isMobile = useIsMobile()
  const leftAxisMetric = activeMetrics[0]
  const rightAxisMetric = activeMetrics[1]

  useEffect(() => {
    fetchData()
    fetchCategories()
  }, [])

  useEffect(() => {
    fetchTrendData()
  }, [trendDays])

  useEffect(() => {
    fetchCalendarMonth(currentMonth)
  }, [currentMonth])

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

  const fetchCalendarMonth = async (month: dayjs.Dayjs) => {
    setCalendarLoading(true)
    try {
      const result = await dietApi.getDateRangeTrend(
        month.startOf('month').format('YYYY-MM-DD'),
        month.endOf('month').format('YYYY-MM-DD'),
      )
      const nextMap = result.dailyStats.reduce<Record<string, {
        calories: number
        protein: number
        carbs: number
        fat: number
        water: number
        mealCount: number
      }>>((acc, item) => {
        acc[item.date] = {
          calories: item.calories,
          protein: item.protein,
          carbs: item.carbs,
          fat: item.fat,
          water: item.water,
          mealCount: item.mealCount,
        }
        return acc
      }, {})
      setCalendarStatsMap(nextMap)
    } catch {
      setCalendarStatsMap({})
    } finally {
      setCalendarLoading(false)
    }
  }

  const resetAddMealDraft = () => {
    addForm.resetFields()
    setSelectedFood(null)
    setMealFilter('')
    setCurrentSearch('')
    setFoodOptions([])
  }

  const openAddDialog = (targetDate?: string) => {
    const nextDate = targetDate || selectedCalendarDate || dayjs().format('YYYY-MM-DD')
    resetAddMealDraft()
    setSelectedCalendarDate(nextDate)
    addForm.setFieldsValue({
      mealType: 'breakfast',
      calories: 0,
      protein: 0,
      carbs: 0,
      fat: 0,
      water: 0,
      mealDate: dayjs(nextDate),
      time: dayjs(),
    })
    setAddOpen(true)
  }

  const handleTrendMetricsChange = (vals: any[]) => {
    const normalized = Array.from(new Set((vals as string[]).filter(Boolean)))
    if (normalized.length === 0) {
      message.info('至少保留一个趋势指标')
      return
    }
    if (normalized.length > 2) {
      message.info('最多选择两个指标，分别对应左右两个 Y 轴')
      setActiveMetrics(normalized.slice(-2))
      return
    }
    setActiveMetrics(normalized)
  }

  const fetchCalendarMeals = async (dateStr: string) => {
    setSelectedCalendarMealsLoading(true)
    try {
      const meals = await dietApi.getTodayMeals(dateStr)
      setSelectedCalendarDate(dateStr)
      setSelectedCalendarMeals(meals)
    } catch {
      setSelectedCalendarDate(dateStr)
      setSelectedCalendarMeals([])
    } finally {
      setSelectedCalendarMealsLoading(false)
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
      setSelectedCalendarDate(dayjs().format('YYYY-MM-DD'))
      setSelectedCalendarMeals(mealsData)
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
      const targetDate = values.mealDate?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD')
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
      await Promise.all([
        fetchData(),
        fetchCalendarMonth(currentMonth),
      ])
      if (selectedCalendarDate === targetDate) {
        fetchCalendarMeals(targetDate)
      }
      if (selectedDate === targetDate) {
        fetchDayMeals(targetDate)
      }
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
      await Promise.all([
        fetchData(),
        fetchCalendarMonth(currentMonth),
      ])
      if (selectedCalendarDate) {
        fetchCalendarMeals(selectedCalendarDate)
      }
      if (selectedDate) {
        fetchDayMeals(selectedDate)
      }
    } catch {
      message.error('更新失败')
    }
  }

  const handleDeleteMeal = async (mealId: number) => {
    try {
      await dietApi.deleteMeal(mealId)
      message.success('删除成功')
      await Promise.all([
        fetchData(),
        fetchCalendarMonth(currentMonth),
      ])
      if (selectedCalendarDate) {
        fetchCalendarMeals(selectedCalendarDate)
      }
      if (selectedDate) {
        fetchDayMeals(selectedDate)
      }
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
      <style>{`
        .diet-calendar .ant-picker-cell-inner { overflow: hidden; max-width: 100%; }
        .diet-calendar .ant-picker-cell { overflow: hidden; }
        .diet-calendar .ant-picker-calendar-date-content { height: auto !important; min-height: 96px; }
        .diet-summary-card .ant-card-body { padding: 16px; }
        .diet-summary-label { font-size: 13px; }
        .diet-summary-value {
          margin: 8px 0 4px !important;
          font-size: 28px !important;
          line-height: 1.15 !important;
          font-weight: 700 !important;
        }
        .diet-summary-progress .ant-progress-text {
          min-width: 34px;
          font-size: 12px !important;
        }
        .diet-nutrition-card .ant-card-body { padding: 18px 18px 16px; }
        .diet-nutrition-title {
          display: block;
          margin-bottom: 10px;
        }
        .diet-nutrition-item {
          height: 100%;
          padding: 12px;
          border-radius: 14px;
          background: #f8fafc;
          border: 1px solid #e2e8f0;
        }
        .diet-nutrition-item-label {
          display: block;
          font-size: 13px;
          line-height: 1.4;
        }
        .diet-nutrition-item .ant-progress {
          margin: 8px 0 6px;
        }
        .diet-nutrition-item .ant-progress-text {
          min-width: 30px;
          font-size: 11px !important;
        }
        @media (max-width: 767px) {
          .diet-calendar .ant-picker-calendar-header { flex-wrap: wrap; }
          .diet-calendar .ant-picker-cell-content { height: auto; }
          .diet-calendar .ant-picker-date-panel .ant-picker-body th { font-size: 12px; padding: 6px 0; }
          .diet-calendar .ant-picker-cell-inner { padding: 0; }
          .diet-calendar .ant-picker-content { font-size: 13px; }
          .diet-summary-card .ant-card-body { padding: 12px; }
          .diet-summary-label { font-size: 12px; }
          .diet-summary-value {
            font-size: 20px !important;
            margin: 6px 0 4px !important;
            word-break: break-word;
          }
          .diet-summary-progress .ant-progress-inner,
          .diet-nutrition-item .ant-progress-inner {
            height: 6px !important;
          }
          .diet-summary-meta {
            display: block;
            font-size: 11px !important;
            line-height: 1.4;
          }
          .diet-nutrition-card .ant-card-body { padding: 12px; }
          .diet-nutrition-title {
            margin-bottom: 8px;
            font-size: 14px !important;
          }
          .diet-nutrition-item {
            padding: 10px 8px;
            border-radius: 12px;
          }
          .diet-nutrition-item-label {
            font-size: 12px;
          }
          .diet-nutrition-value {
            display: block;
            font-size: 11px !important;
            line-height: 1.35;
          }
        }
      `}</style>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#ECFEFF', color: '#06B6D4' }}>
          <Utensils size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>饮食管理</Typography.Title>
      </div>

      <Row gutter={[isMobile ? 8 : 16, isMobile ? 8 : 16]}>
        <Col xs={8} sm={8} md={8}>
          <Card className="fitagent-card-hover diet-summary-card" style={{ border: 'none', background: 'linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%)' }}>
            <Typography.Text type="secondary" className="diet-summary-label">今日热量</Typography.Text>
            <Typography.Title level={3} className="diet-summary-value" style={{ color: '#EF4444' }}>
              {loading ? '-' : `${stats?.calories || 0} / ${stats?.caloriesGoal || 2000} kcal`}
            </Typography.Title>
            <Progress
              className="diet-summary-progress"
              percent={getProgressPercent(stats?.calories || 0, stats?.caloriesGoal || 2000)}
              strokeColor="#10B981"
              showInfo={!isMobile}
            />
            <Typography.Text type="secondary" className="diet-summary-meta">剩余 {stats?.remainingCalories || 0} kcal</Typography.Text>
          </Card>
        </Col>
        <Col xs={8} sm={8} md={8}>
          <Card className="fitagent-card-hover diet-summary-card" style={{ background: '#F5F5F5', border: '1px solid #e8e8e8' }}>
            <Typography.Text type="secondary" className="diet-summary-label">连续记录</Typography.Text>
            <Typography.Title level={3} className="diet-summary-value">{loading ? '-' : `${stats?.streakDays || 0} 天`}</Typography.Title>
            <Typography.Text type="secondary" className="diet-summary-meta">保持节奏更容易形成习惯</Typography.Text>
          </Card>
        </Col>
        <Col xs={8} sm={8} md={8}>
          <Card className="fitagent-card-hover diet-summary-card" style={{ border: 'none', background: 'linear-gradient(135deg, #E0F2FE 0%, #BAE6FD 100%)' }}>
            <Typography.Text type="secondary" className="diet-summary-label">饮水</Typography.Text>
            <Typography.Title level={3} className="diet-summary-value" style={{ color: '#0EA5E9' }}>{loading ? '-' : `${stats?.water || 0} / ${stats?.waterGoal || 2000} ml`}</Typography.Title>
            <Progress
              className="diet-summary-progress"
              percent={getProgressPercent(stats?.water || 0, stats?.waterGoal || 2000)}
              strokeColor="#0EA5E9"
              showInfo={!isMobile}
            />
          </Card>
        </Col>
      </Row>

      <Card className="diet-nutrition-card" style={{ marginTop: isMobile ? 12 : 24, border: 'none' }}>
        <Typography.Title level={5} className="diet-nutrition-title">今日营养摄入</Typography.Title>
        <Row gutter={isMobile ? 8 : 12} style={{ marginTop: 0 }}>
          <Col xs={8} sm={8}>
            <div className="diet-nutrition-item">
              <Typography.Text className="diet-nutrition-item-label">蛋白质</Typography.Text>
              <Progress
                percent={getProgressPercent(stats?.protein || 0, stats?.proteinGoal || 150)}
                strokeColor="#10B981"
                showInfo={!isMobile}
              />
              <Typography.Text type="secondary" className="diet-nutrition-value">{stats?.protein || 0}/{stats?.proteinGoal || 150}g</Typography.Text>
            </div>
          </Col>
          <Col xs={8} sm={8}>
            <div className="diet-nutrition-item">
              <Typography.Text className="diet-nutrition-item-label">碳水</Typography.Text>
              <Progress
                percent={getProgressPercent(stats?.carbs || 0, stats?.carbsGoal || 250)}
                strokeColor="#F59E0B"
                showInfo={!isMobile}
              />
              <Typography.Text type="secondary" className="diet-nutrition-value">{stats?.carbs || 0}/{stats?.carbsGoal || 250}g</Typography.Text>
            </div>
          </Col>
          <Col xs={8} sm={8}>
            <div className="diet-nutrition-item">
              <Typography.Text className="diet-nutrition-item-label">脂肪</Typography.Text>
              <Progress
                percent={getProgressPercent(stats?.fat || 0, stats?.fatGoal || 65)}
                strokeColor="#EF4444"
                showInfo={!isMobile}
              />
              <Typography.Text type="secondary" className="diet-nutrition-value">{stats?.fat || 0}/{stats?.fatGoal || 65}g</Typography.Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* 饮食趋势图表 */}
      <Card className="fitagent-trend-panel" style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <div className="fitagent-trend-toolbar">
          <div>
            <Typography.Title level={5} className="fitagent-trend-title">饮食趋势</Typography.Title>
            <Typography.Text className="fitagent-trend-subtitle">
              查看近阶段热量与营养摄入变化，点击节点可查看当天饮食记录
            </Typography.Text>
          </div>
          <Radio.Group className="fitagent-trend-radio" value={trendDays} onChange={e => setTrendDays(e.target.value)} size="small">
            <Radio.Button value={7}>近7天</Radio.Button>
            <Radio.Button value={14}>近14天</Radio.Button>
            <Radio.Button value={30}>近30天</Radio.Button>
          </Radio.Group>
        </div>

        <Checkbox.Group
          className="fitagent-trend-metrics"
          value={activeMetrics}
          onChange={handleTrendMetricsChange}
        >
          <Space wrap size={8}>
            <Checkbox value="calories">热量</Checkbox>
            <Checkbox value="protein">蛋白质</Checkbox>
            <Checkbox value="carbs">碳水</Checkbox>
            <Checkbox value="fat">脂肪</Checkbox>
          </Space>
        </Checkbox.Group>

        <div className="fitagent-chart-shell">
        <ResponsiveContainer width="100%" height={isMobile ? 200 : 260}>
          <LineChart data={trendLoading ? [] : trendData} onClick={(e: any) => {
            if (e?.activePayload?.[0]?.payload?.date) {
              const idx = trendData.findIndex(d => d.date === e.activePayload[0].payload.date)
              if (idx >= 0) {
                fetchDayMeals(trendData[idx].fullDate || trendData[idx].date)
              }
            }
          }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#dbeafe" vertical={false} />
            <XAxis
              dataKey="date"
              tick={{ fontSize: isMobile ? 11 : 12, fill: '#64748b' }}
              tickLine={false}
              axisLine={{ stroke: '#cbd5e1' }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fontSize: isMobile ? 11 : 12, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              hide={!leftAxisMetric}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: isMobile ? 11 : 12, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              hide={!rightAxisMetric}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 16,
                border: '1px solid #dbeafe',
                boxShadow: '0 14px 32px rgba(14, 165, 233, 0.12)',
                background: 'rgba(255,255,255,0.96)',
              }}
              labelStyle={{ color: '#0f172a', fontWeight: 600, marginBottom: 6 }}
              itemStyle={{ color: '#334155' }}
              formatter={(value: any, name: any) => {
                return [`${value}${METRIC_STYLES[name]?.unit || ''}`, METRIC_STYLES[name]?.label || name]
              }}
            />
            {leftAxisMetric && (
              <Line
                type="monotone"
                yAxisId="left"
                dataKey={leftAxisMetric}
                name={leftAxisMetric}
                stroke={METRIC_STYLES[leftAxisMetric].color}
                strokeWidth={3}
                dot={{ r: 0 }}
                activeDot={{ r: 5, strokeWidth: 0, fill: METRIC_STYLES[leftAxisMetric].color }}
                {...sharedTrendLineMotion}
              />
            )}
            {rightAxisMetric && (
              <Line
                type="monotone"
                yAxisId="right"
                dataKey={rightAxisMetric}
                name={rightAxisMetric}
                stroke={METRIC_STYLES[rightAxisMetric].color}
                strokeWidth={3}
                dot={{ r: 0 }}
                activeDot={{ r: 5, strokeWidth: 0, fill: METRIC_STYLES[rightAxisMetric].color }}
                {...sharedTrendLineMotion}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
        </div>

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

      <Card className="fitagent-trend-panel" style={{ marginTop: isMobile ? 16 : 24, border: 'none' }}>
        <div className="fitagent-trend-toolbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button
              size="small"
              icon={<LeftOutlined />}
              onClick={() => setCurrentMonth((month) => month.subtract(1, 'month'))}
            />
            <Typography.Title level={5} className="fitagent-trend-title">
              {currentMonth.format('YYYY年M月')} 饮食日历
            </Typography.Title>
            <Button
              size="small"
              icon={<RightOutlined />}
              onClick={() => setCurrentMonth((month) => month.add(1, 'month'))}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <Typography.Text className="fitagent-trend-subtitle">
              点击日期查看当天详细饮食卡片
            </Typography.Text>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openAddDialog(selectedCalendarDate)}>
              添加记录
            </Button>
          </div>
        </div>

        <div className="fitagent-chart-shell" style={{ paddingBottom: 12 }}>
          <Calendar
            className="diet-calendar"
            fullscreen={!isMobile}
            mode="month"
            value={currentMonth}
            onSelect={(value) => fetchCalendarMeals(value.format('YYYY-MM-DD'))}
            onPanelChange={(value, mode) => {
              if (mode === 'month') {
                setCurrentMonth(value)
              }
            }}
            cellRender={(date) => {
              const dateStr = date.format('YYYY-MM-DD')
              const daily = calendarStatsMap[dateStr]
              const isToday = date.isSame(dayjs(), 'day')
              const isSelected = selectedCalendarDate === dateStr
              const isCurrentMonth = date.month() === currentMonth.month()

              return (
                <div
                  onClick={() => fetchCalendarMeals(dateStr)}
                  style={{
                    minHeight: isMobile ? 82 : 112,
                    height: '100%',
                    padding: '6px 8px',
                    position: 'relative',
                    borderRadius: 12,
                    cursor: 'pointer',
                    border: isSelected
                      ? '1px solid #38bdf8'
                      : daily?.mealCount
                        ? '1px solid #dbeafe'
                        : '1px solid transparent',
                    background: isSelected
                      ? 'linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 100%)'
                      : daily?.mealCount
                        ? 'linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)'
                        : isCurrentMonth
                          ? '#fafcff'
                          : '#f8fafc',
                    boxShadow: isSelected ? '0 10px 24px rgba(14, 165, 233, 0.12)' : 'none',
                    opacity: isCurrentMonth ? 1 : 0.58,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 6,
                  }}
                >
                  <div
                    style={{
                      fontSize: isMobile ? 13 : 15,
                      fontWeight: isToday || isSelected ? 700 : 500,
                      color: isToday ? '#0284c7' : '#0f172a',
                    }}
                  >
                    {date.date()}
                  </div>
                  <Button
                    size="small"
                    type="text"
                    icon={<PlusOutlined />}
                    onClick={(event) => {
                      event.stopPropagation()
                      openAddDialog(dateStr)
                    }}
                    style={{
                      position: 'absolute',
                      top: 4,
                      right: 4,
                      width: 24,
                      height: 24,
                      minWidth: 24,
                      padding: 0,
                      borderRadius: 999,
                      color: '#0284c7',
                      background: isSelected ? 'rgba(255,255,255,0.86)' : 'rgba(240,249,255,0.92)',
                    }}
                  />
                  {daily?.mealCount ? (
                    <>
                      <div
                        style={{
                          display: 'inline-flex',
                          alignSelf: 'flex-start',
                          padding: '2px 8px',
                          borderRadius: 999,
                          background: '#e0f2fe',
                          color: '#0369a1',
                          fontSize: 12,
                          fontWeight: 600,
                        }}
                      >
                        {daily.mealCount} 条记录
                      </div>
                      <div style={{ fontSize: 12, color: '#475569', lineHeight: 1.5 }}>
                        {daily.calories} kcal
                      </div>
                      <div style={{ fontSize: 12, color: '#94a3b8' }}>
                        P {daily.protein}g / C {daily.carbs}g
                      </div>
                    </>
                  ) : (
                    <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 4 }}>
                      暂无记录
                    </div>
                  )}
                </div>
              )
            }}
          />
        </div>

        <div style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, gap: 12, flexWrap: 'wrap' }}>
            <div>
              <Typography.Text strong style={{ fontSize: 15 }}>
                {dayjs(selectedCalendarDate).format('YYYY-MM-DD')} 饮食详情
              </Typography.Text>
              <div style={{ marginTop: 6 }}>
                <Typography.Text type="secondary">
                  {calendarStatsMap[selectedCalendarDate]?.mealCount || selectedCalendarMeals.length} 条记录
                  {' · '}
                  {calendarStatsMap[selectedCalendarDate]?.calories || 0} kcal
                </Typography.Text>
              </div>
            </div>
            {calendarLoading && <Typography.Text type="secondary">月历加载中...</Typography.Text>}
          </div>

          {selectedCalendarMealsLoading ? (
            <Card loading style={{ borderRadius: 20, border: '1px solid #e2e8f0' }} />
          ) : selectedCalendarMeals.length ? (
            <Row gutter={[12, 12]}>
              {selectedCalendarMeals.map((item) => (
                <Col xs={24} md={12} xl={8} key={item.mealId}>
                  <Card
                    className="fitagent-card-hover"
                    size="small"
                    style={{
                      borderRadius: 20,
                      border: '1px solid #dbeafe',
                      background: 'linear-gradient(180deg, #ffffff 0%, #f8fbff 100%)',
                    }}
                    bodyStyle={{ padding: 16 }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
                      <div style={{ minWidth: 0 }}>
                        <Space size={8} wrap>
                          {getMealTypeTag(item.mealType)}
                          <Typography.Text type="secondary">{item.time}</Typography.Text>
                        </Space>
                        <Typography.Title level={5} style={{ margin: '10px 0 0', fontSize: 18 }}>
                          {item.mealName}
                        </Typography.Title>
                      </div>
                      <Avatar style={{ backgroundColor: CALORIE_LEVEL_COLORS[item.mealType] || '#0EA5E9', flexShrink: 0 }}>
                        {item.mealName.charAt(0)}
                      </Avatar>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: 10, marginTop: 16 }}>
                      <div style={{ padding: '10px 12px', borderRadius: 14, background: '#fff1f2' }}>
                        <Typography.Text type="secondary">热量</Typography.Text>
                        <div style={{ marginTop: 4, fontWeight: 700, color: '#e11d48' }}>{item.calories} kcal</div>
                      </div>
                      <div style={{ padding: '10px 12px', borderRadius: 14, background: '#f0fdf4' }}>
                        <Typography.Text type="secondary">蛋白质</Typography.Text>
                        <div style={{ marginTop: 4, fontWeight: 700, color: '#16a34a' }}>{item.protein} g</div>
                      </div>
                      <div style={{ padding: '10px 12px', borderRadius: 14, background: '#fffbeb' }}>
                        <Typography.Text type="secondary">碳水</Typography.Text>
                        <div style={{ marginTop: 4, fontWeight: 700, color: '#d97706' }}>{item.carbs} g</div>
                      </div>
                      <div style={{ padding: '10px 12px', borderRadius: 14, background: '#faf5ff' }}>
                        <Typography.Text type="secondary">脂肪</Typography.Text>
                        <div style={{ marginTop: 4, fontWeight: 700, color: '#7c3aed' }}>{item.fat} g</div>
                      </div>
                    </div>

                    {item.note && (
                      <div style={{ marginTop: 14, padding: '10px 12px', borderRadius: 14, background: '#f8fafc', color: '#475569', lineHeight: 1.6 }}>
                        {item.note}
                      </div>
                    )}

                    <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
                      <Button size="small" icon={<EditOutlined />} onClick={() => openEditDialog(item)}>
                        编辑
                      </Button>
                      <Button size="small" danger icon={<DeleteOutlined />} onClick={() => handleDeleteMeal(item.mealId)}>
                        删除
                      </Button>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <Card
              size="small"
              style={{
                borderRadius: 20,
                border: '1px dashed #cbd5e1',
                background: '#f8fafc',
              }}
              bodyStyle={{ padding: 20, textAlign: 'center' }}
            >
              <Typography.Text type="secondary">
                这一天还没有饮食记录，可以直接点击该日期右上角的加号快速补充。
              </Typography.Text>
              <div style={{ marginTop: 12 }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={() => openAddDialog(selectedCalendarDate)}>
                  为这一天添加记录
                </Button>
              </div>
            </Card>
          )}
        </div>
      </Card>

      {/* Add Meal Modal */}
      <Modal
        title="添加饮食记录"
        open={addOpen}
        onCancel={() => { setAddOpen(false); resetAddMealDraft() }}
        onOk={handleAddMeal}
        okText="提交"
        cancelText="取消"
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        <Form form={addForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ mealDate: dayjs(), mealType: 'breakfast', calories: 0, protein: 0, carbs: 0, fat: 0, water: 0, time: dayjs() }}>
          <Form.Item name="mealType" label="餐次类型" rules={[{ required: true }]}>
            <Select options={mealTypes} />
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
              popupRender={(menu) => (
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
            <Col xs={12}><Form.Item name="calories" label="热量" rules={[{ required: true }]}><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>kcal</Button></Space.Compact></Form.Item></Col>
            <Col xs={12}><Form.Item name="protein" label="蛋白质"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
          </Row>
          <Row gutter={16}>
            <Col xs={12}><Form.Item name="carbs" label="碳水"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
            <Col xs={12}><Form.Item name="fat" label="脂肪"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
          </Row>
          <Form.Item name="water" label="饮水"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>ml</Button></Space.Compact></Form.Item>
          <Form.Item name="mealDate" label="日期" rules={[{ required: true }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="time" label="时间" rules={[{ required: true }]}>
            <TimePicker style={{ width: '100%' }} />
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
        <Form form={customFoodForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ protein: 0, carbs: 0, fat: 0 }}>
          <Form.Item name="name" label="食物名称" rules={[{ required: true }]}>
            <Input placeholder="如：自制燕麦饼干" />
          </Form.Item>
          <Form.Item name="category" label="分类" rules={[{ required: true }]}>
            <Select placeholder="选择分类" options={foodCategories.map(c => ({ label: c, value: c }))} />
          </Form.Item>
          <Row gutter={16}>
            <Col xs={12}><Form.Item name="portionUnit" label="一份单位"><Input placeholder="如：1 块" /></Form.Item></Col>
            <Col xs={12}><Form.Item name="portionGrams" label="一份克数"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
          </Row>
          <Form.Item name="portionCalories" label="一份热量" rules={[{ required: true }]}>
            <Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>kcal</Button></Space.Compact>
          </Form.Item>
          <Form.Item name="caloriesPer100g" label="每100g热量" rules={[{ required: true }]}>
            <Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>kcal</Button></Space.Compact>
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
            <Col xs={8}><Form.Item name="protein" label="蛋白质"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
            <Col xs={8}><Form.Item name="carbs" label="碳水"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
            <Col xs={8}><Form.Item name="fat" label="脂肪"><Space.Compact style={{ width: '100%' }}><InputNumber style={{ flex: 1 }} /><Button disabled>g</Button></Space.Compact></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </div>
  )
}

export default Diet
