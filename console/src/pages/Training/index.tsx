import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Button, Modal, Form, Input, InputNumber, Select, DatePicker, Calendar, Tag, Space, message, Radio, Checkbox, List, Avatar, Popconfirm } from 'antd'
import { PlusOutlined, CheckOutlined, SyncOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import { Dumbbell } from 'lucide-react'
import dayjs from 'dayjs'
import type { Dayjs } from 'dayjs'
import api from '../../utils/request'
import { trainingApi, type WeeklyStats, type PlanDetail, PlanExerciseItemOutput } from '../../services/training'
import { PlanExerciseInput } from '../../services/exercise'
import ExercisePicker from '../../components/ExercisePicker'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import 'dayjs/locale/zh-cn'

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

const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])
  return isMobile
}

const Training: React.FC = () => {
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [monthSchedule, setMonthSchedule] = useState<{ planId?: number; date: string; planName: string; planType: string; duration: number; intensity: string; status: string; isRecurring?: boolean; isLastInGroup?: boolean }[]>([])
  const [loading, setLoading] = useState(true)
  const [currentMonth, setCurrentMonth] = useState<Dayjs>(dayjs())
  const [createOpen, setCreateOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)
  const [createForm] = Form.useForm()
  const [completeForm] = Form.useForm()

  const [trendDays, setTrendDays] = useState(7)
  const [trendLoading, setTrendLoading] = useState(false)
  const [trendData, setTrendData] = useState<any[]>([])
  const [activeMetrics, setActiveMetrics] = useState<string[]>(['duration', 'caloriesBurned'])

  const [exercisePickerOpen, setExercisePickerOpen] = useState(false)
  const [selectedExercises, setSelectedExercises] = useState<PlanExerciseInput[]>([])
  const [customName, setCustomName] = useState('')
  const [customSets, setCustomSets] = useState(3)
  const [customReps, setCustomReps] = useState(10)
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailData, setDetailData] = useState<PlanDetail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [editingExerciseId, setEditingExerciseId] = useState<number | null>(null)
  const [editingDraft, setEditingDraft] = useState<{ sets: number; reps: number; weight: number | null } | null>(null)
  const [detailPlanInfo, setDetailPlanInfo] = useState<{ isRecurring?: boolean; isLastInGroup?: boolean } | null>(null)
  const [detailExercisePickerOpen, setDetailExercisePickerOpen] = useState(false)
  const [detailCustomName, setDetailCustomName] = useState('')
  const [detailCustomSets, setDetailCustomSets] = useState(3)
  const [detailCustomReps, setDetailCustomReps] = useState(10)

  const isMobile = useIsMobile()

  const handleRenewPlan = async (planId: number) => {
    try {
      await api.post(`/training/plans/${planId}/renew`)
      message.success('续期成功')
      fetchData()
    } catch { message.error('续期失败') }
  }

  useEffect(() => {
    fetchData()
  }, [currentMonth])

  useEffect(() => {
    fetchTrendData()
  }, [trendDays])

  const fetchTrendData = async () => {
    setTrendLoading(true)
    try {
      const end = dayjs()
      const start = end.subtract(trendDays - 1, 'day')
      const result = await trainingApi.getDateRangeTrend(start.format('YYYY-MM-DD'), end.format('YYYY-MM-DD'))
      const formatted = result.dailyStats.map(d => ({ ...d, date: dayjs(d.date).format('MM/DD') }))
      setTrendData(formatted)
    } catch { /* ignore */ } finally { setTrendLoading(false) }
  }

  const fetchData = async () => {
    setLoading(true)
    try {
      const [stats, sched] = await Promise.all([
        trainingApi.getWeeklyStats(),
        trainingApi.getMonthlySchedule(currentMonth.year(), currentMonth.month() + 1),
      ])
      setWeeklyStats(stats)
      setMonthSchedule(sched)
    } finally { setLoading(false) }
  }

  const handleCreatePlan = async () => {
    try {
      const values = await createForm.validateFields()
      await trainingApi.createPlan({
        ...values,
        estimatedDuration: values.estimatedDuration,
        scheduledDate: values.scheduledDate.format('YYYY-MM-DD'),
        isRecurring: values.isRecurring || false,
        exercises: selectedExercises.length > 0 ? selectedExercises : undefined,
      })
      message.success('创建成功')
      setCreateOpen(false)
      createForm.resetFields()
      setSelectedExercises([])
      fetchData()
    } catch { message.error('创建失败') }
  }

  const handleCompletePlan = async () => {
    if (!selectedPlanId) {
      message.error('请先选择计划')
      return
    }
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
    } catch (e: any) {
      message.error(e.message || '记录失败')
    }
  }

  const handleDeletePlan = async (planId: number) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该训练计划吗？相关训练记录也会被一并删除。',
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try { await trainingApi.deletePlan(planId); message.success('删除成功'); fetchData() }
        catch { message.error('删除失败') }
      },
    })
  }

  const handleViewDetail = async (planId: number) => {
    setDetailLoading(true)
    setDetailOpen(true)
    try {
      const detail = await trainingApi.getPlanDetail(planId)
      setDetailData(detail)
      const schedItem = monthSchedule.find(s => s.planId === planId)
      setDetailPlanInfo(schedItem ? { isRecurring: schedItem.isRecurring, isLastInGroup: schedItem.isLastInGroup } : null)
    } catch { message.error('获取详情失败') } finally { setDetailLoading(false) }
  }

  const handleAddExercisesToDetail = async (exercises: PlanExerciseInput[]) => {
    if (!detailData) return
    try {
      for (const ex of exercises) {
        await trainingApi.addPlanExercise(detailData.planId, ex)
      }
      message.success('添加成功')
      setDetailExercisePickerOpen(false)
      // 重新加载详情
      handleViewDetail(detailData.planId)
    } catch { message.error('添加失败') }
  }

  const handleAddCustomExerciseToDetail = async () => {
    if (!detailData) return
    if (!detailCustomName.trim()) { message.warning('请输入动作名称'); return }
    try {
      await trainingApi.addPlanExercise(detailData.planId, {
        customName: detailCustomName.trim(),
        sets: detailCustomSets,
        reps: detailCustomReps,
      })
      message.success('添加成功')
      setDetailCustomName('')
      handleViewDetail(detailData.planId)
    } catch { message.error('添加失败') }
  }

  const handleDeleteExerciseFromDetail = async (exerciseId: number) => {
    try {
      await trainingApi.deletePlanExercise(exerciseId)
      message.success('删除成功')
      if (detailData) {
        setDetailData(prev => prev ? { ...prev, exercises: prev.exercises.filter(e => e.id !== exerciseId) } : prev)
      }
    } catch { message.error('删除失败') }
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
    <div className="fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <style>{`
        .training-calendar .ant-picker-cell-inner { overflow: hidden; max-width: 100%; }
        .training-calendar .ant-picker-cell { overflow: hidden; }
        .training-calendar .ant-picker-calendar-date-content { height: auto !important; min-height: 100px; }
        @media (max-width: 767px) {
          .training-calendar .ant-picker-calendar-header { flex-wrap: wrap; }
          .training-calendar .ant-picker-cell-content { height: auto; }
          .training-calendar .ant-picker-date-panel .ant-picker-body th { font-size: 12px; padding: 6px 0; }
          .training-calendar .ant-picker-cell-inner { padding: 0; }
          .training-calendar .ant-picker-content { font-size: 13px; }
          .fitagent-page-enter .ant-modal { padding-bottom: 0; }
          .fitagent-page-enter .ant-modal-body { padding: 16px; max-height: 80vh; overflow-y: auto; }
        }
      `}</style>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#FFF7ED', color: '#F59E0B' }}>
          <Dumbbell size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>训练计划</Typography.Title>
      </div>

      <Row gutter={[isMobile ? 8 : 12, isMobile ? 8 : 12]}>
        <Col xs={12} sm={6} md={6}>
          <div className="fitagent-card-hover" style={{
            padding: isMobile ? 12 : 16,
            borderRadius: 6,
            background: '#F0FDF4',
            border: '1px solid #86EFAC',
            height: '100%',
          }}>
            <Typography.Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>本周训练</Typography.Text>
            <div style={{ fontSize: isMobile ? 22 : 28, fontWeight: 700, color: '#10B981', marginTop: 8 }}>
              {loading ? '-' : `${weeklyStats?.weeklyCount || 0}`}
              <span style={{ fontSize: isMobile ? 12 : 14, fontWeight: 500, marginLeft: 4 }}>次</span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div className="fitagent-card-hover" style={{
            padding: isMobile ? 12 : 16,
            borderRadius: 6,
            background: '#F5F5F5',
            border: '1px solid #e8e8e8',
            height: '100%',
          }}>
            <Typography.Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>本周时长</Typography.Text>
            <div style={{ fontSize: isMobile ? 22 : 28, fontWeight: 700, marginTop: 8 }}>
              {loading ? '-' : `${weeklyStats?.weeklyHours || 0}`}
              <span style={{ fontSize: isMobile ? 12 : 14, fontWeight: 500, marginLeft: 4 }}>小时</span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div className="fitagent-card-hover" style={{
            padding: isMobile ? 12 : 16,
            borderRadius: 6,
            background: '#FFF7ED',
            border: '1px solid #FED7AA',
            height: '100%',
          }}>
            <Typography.Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>消耗热量</Typography.Text>
            <div style={{ fontSize: isMobile ? 22 : 28, fontWeight: 700, color: '#F59E0B', marginTop: 8 }}>
              {loading ? '-' : `${weeklyStats?.weeklyCalories || 0}`}
              <span style={{ fontSize: isMobile ? 12 : 14, fontWeight: 500, marginLeft: 4 }}>kcal</span>
            </div>
          </div>
        </Col>
        <Col xs={12} sm={6} md={6}>
          <div className="fitagent-card-hover" style={{
            padding: isMobile ? 12 : 16,
            borderRadius: 6,
            background: '#F5F3FF',
            border: '1px solid #DDD6FE',
            height: '100%',
          }}>
            <Typography.Text type="secondary" style={{ fontSize: isMobile ? 12 : 13 }}>连续训练</Typography.Text>
            <div style={{ fontSize: isMobile ? 22 : 28, fontWeight: 700, color: '#8B5CF6', marginTop: 8 }}>
              {loading ? '-' : `${weeklyStats?.streakDays || 0}`}
              <span style={{ fontSize: isMobile ? 12 : 14, fontWeight: 500, marginLeft: 4 }}>天</span>
            </div>
          </div>
        </Col>
      </Row>

      <div style={{
        marginTop: isMobile ? 16 : 24,
        padding: isMobile ? 12 : 16,
        borderRadius: 6,
        background: '#F5F5F5',
        border: '1px solid #e8e8e8',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <Typography.Text strong style={{ fontSize: isMobile ? 14 : 16 }}>训练趋势</Typography.Text>
          <Radio.Group value={trendDays} onChange={e => setTrendDays(e.target.value)} size="small">
            <Radio.Button value={7}>近7天</Radio.Button>
            <Radio.Button value={14}>近14天</Radio.Button>
            <Radio.Button value={30}>近30天</Radio.Button>
          </Radio.Group>
        </div>

        <Checkbox.Group value={activeMetrics} onChange={(vals: any[]) => setActiveMetrics(vals)} style={{ marginBottom: 12 }}>
          <Space wrap size={8}>
            <Checkbox value="duration">时长</Checkbox>
            <Checkbox value="caloriesBurned">消耗热量</Checkbox>
          </Space>
        </Checkbox.Group>

        <ResponsiveContainer width="100%" height={isMobile ? 200 : 260}>
          <LineChart data={trendLoading ? [] : trendData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
            <XAxis dataKey="date" tick={{ fontSize: isMobile ? 11 : 12 }} />
            <YAxis yAxisId="left" tick={{ fontSize: isMobile ? 11 : 12 }} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: isMobile ? 11 : 12 }} />
            <Tooltip formatter={(value: any, name: any) => {
              const labels: Record<string, string> = { duration: '时长', caloriesBurned: '消耗热量', planCount: '计划数' }
              const units: Record<string, string> = { duration: ' 分钟', caloriesBurned: ' kcal' }
              return [`${value}${units[name] || ''}`, labels[name] || name]
            }} />
            {activeMetrics.includes('duration') && <Line type="monotone" yAxisId="left" dataKey="duration" name="duration" stroke="#10B981" strokeWidth={2} dot={{ r: 3 }} />}
            {activeMetrics.includes('caloriesBurned') && <Line type="monotone" yAxisId="right" dataKey="caloriesBurned" name="caloriesBurned" stroke="#F59E0B" strokeWidth={2} dot={{ r: 3 }} />}
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div style={{
        marginTop: isMobile ? 16 : 24,
        padding: isMobile ? 12 : 16,
        borderRadius: 6,
        background: '#F5F5F5',
        border: '1px solid #e8e8e8',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button size="small" icon={<LeftOutlined />} onClick={() => setCurrentMonth(m => m.subtract(1, 'month'))} />
            <Typography.Text strong style={{ fontSize: isMobile ? 14 : 16 }}>{currentMonth.format('YYYY年M月')}</Typography.Text>
            <Button size="small" icon={<RightOutlined />} onClick={() => setCurrentMonth(m => m.add(1, 'month'))} />
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)} size={isMobile ? "small" : "middle"}>新建计划</Button>
        </div>

        <Calendar
          className="training-calendar"
          fullscreen={!isMobile}
          mode="month"
          value={currentMonth}
          onPanelChange={(_, mode) => { if (mode === 'month') setCurrentMonth(_) }}
          cellRender={(date) => {
            const dateStr = date.format('YYYY-MM-DD')
            const dayPlans = monthSchedule.filter(s => s.date === dateStr)
            const isToday = date.isSame(dayjs(), 'day')
            const isCurrentMonth = date.month() === currentMonth.month()
            const hasCompleted = dayPlans.some(p => p.status === 'completed')
            const isFuture = date.isAfter(dayjs(), 'day')

            if (dayPlans.length === 0) {
              return (
                <div style={{
                  minHeight: isMobile ? 80 : 120,
                  height: '100%',
                  borderLeft: isToday ? '3px solid #10B981' : 'none',
                  padding: '4px 6px',
                  background: isCurrentMonth && !isToday ? '#FAFFFE' : undefined,
                  width: '100%',
                }}>
                  <div style={{ fontWeight: isToday ? 700 : 400, color: isToday ? '#10B981' : !isCurrentMonth ? '#ccc' : undefined, fontSize: isMobile ? 14 : 16 }}>
                    {date.date()}
                  </div>
                </div>
              )
            }

            return (
              <div style={{
                minHeight: isMobile ? 80 : 120,
                height: '100%',
                borderLeft: isToday ? '3px solid #10B981' : hasCompleted ? '3px solid #10B981' : 'none',
                padding: '4px 6px',
                overflow: 'hidden',
                background: isCurrentMonth && !isToday ? '#FAFFFE' : undefined,
                width: '100%',
              }}>
                <div style={{ fontWeight: isToday ? 700 : 400, color: isToday ? '#10B981' : undefined, fontSize: isMobile ? 14 : 16, marginBottom: 4 }}>
                  {date.date()}
                </div>
                {dayPlans.slice(0, isMobile ? 2 : 3).map(item => (
                  <div
                    key={item.planId}
                    style={{
                      marginTop: 0,
                      marginBottom: 4,
                      padding: '6px 8px',
                      borderRadius: 6,
                      fontSize: isMobile ? 12 : 13,
                      background: item.status === 'completed' ? '#F0FDF4' : '#F5F5F5',
                      border: item.status === 'completed' ? '1px solid #86EFAC' : '1px solid #e8e8e8',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 6,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {item.status === 'completed' && <CheckOutlined style={{ color: '#10B981', fontSize: isMobile ? 12 : 14, flexShrink: 0 }} />}
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 8px',
                        borderRadius: 4,
                        fontSize: isMobile ? 11 : 12,
                        lineHeight: '18px',
                        background: (() => {
                          const colors: Record<string, string> = { strength: '#F59E0B20', cardio: '#10B98120', flexibility: '#0EA5E920' }
                          return colors[item.planType] || '#eee'
                        })(),
                        color: (() => {
                          const colors: Record<string, string> = { strength: '#F59E0B', cardio: '#10B981', flexibility: '#0EA5E9' }
                          return colors[item.planType] || '#666'
                        })(),
                        flexShrink: 0,
                        fontWeight: 600,
                      }}>
                        {(() => {
                          const labels: Record<string, string> = { strength: '力量', cardio: '有氧', flexibility: '柔韧' }
                          return labels[item.planType] || item.planType
                        })()}
                      </span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', cursor: 'pointer', flex: 1, minWidth: 0, fontWeight: 500 }} onClick={() => item.planId && item.planId > 0 && handleViewDetail(item.planId)}>
                        {item.planName}
                      </span>
                    </div>
                    <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-start' }}>
                      {item.status !== 'completed' && (
                        <span style={{ color: isFuture ? '#ccc' : '#1677ff', cursor: isFuture ? 'not-allowed' : 'pointer', fontSize: isMobile ? 12 : 13, lineHeight: '18px', fontWeight: 500 }} onClick={isFuture ? undefined : () => { setSelectedPlanId(item.planId!); setCompleteOpen(true) }}>
                          {isFuture ? '未到' : '打卡'}
                        </span>
                      )}
                      <span style={{ color: '#ff4d4f', cursor: 'pointer', fontSize: isMobile ? 12 : 13, lineHeight: '18px', fontWeight: 500 }} onClick={() => item.planId && handleDeletePlan(item.planId)}>删除</span>
                      {item.isRecurring && item.isLastInGroup && (
                        <span style={{ color: '#1677ff', cursor: 'pointer', fontSize: isMobile ? 12 : 13, lineHeight: '18px', fontWeight: 500 }} onClick={() => item.planId && handleRenewPlan(item.planId)}>续期</span>
                      )}
                    </div>
                  </div>
                ))}
                {dayPlans.length > (isMobile ? 2 : 3) && (
                  <div style={{ fontSize: isMobile ? 11 : 12, color: '#999', marginTop: 2, fontWeight: 500 }}>+{dayPlans.length - (isMobile ? 2 : 3)} 更多</div>
                )}
              </div>
            )
          }}
        />
      </div>

      <Modal title="创建训练计划" open={createOpen} onCancel={() => { setCreateOpen(false); setSelectedExercises([]) }} onOk={handleCreatePlan} okText="创建" cancelText="取消" width={isMobile ? '100%' : undefined} style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}>
        <Form form={createForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="planName" label="计划名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="planType" label="训练类型" rules={[{ required: true }]}><Select options={planTypes} /></Form.Item>
          <Row gutter={16}>
            <Col xs={12}><Form.Item name="targetIntensity" label="目标强度" rules={[{ required: true }]}><Select options={intensities} /></Form.Item></Col>
            <Col xs={12}><Form.Item name="estimatedDuration" label="预计时长" rules={[{ required: true }]}><InputNumber addonAfter="分钟" style={{ width: '100%' }} defaultValue={60} /></Form.Item></Col>
          </Row>
          <Form.Item name="scheduledDate" label="计划日期" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} defaultValue={dayjs()} /></Form.Item>
          <Form.Item name="isRecurring" valuePropName="checked" initialValue={false}>
            <Checkbox><SyncOutlined /> 每周循环（按周几自动复用）</Checkbox>
          </Form.Item>
          <Form.Item label="训练动作">
            <Space direction="vertical" style={{ width: '100%' }} size={8}>
              <Space wrap>
                <Button icon={<PlusOutlined />} onClick={() => setExercisePickerOpen(true)}>从动作库选择</Button>
                <Button type="dashed" icon={<PlusOutlined />} onClick={() => {
                  if (!customName.trim()) { message.warning('请输入动作名称'); return }
                  setSelectedExercises((prev) => [...prev, { customName: customName.trim(), sets: customSets, reps: customReps }])
                  setCustomName('')
                }}>添加自定义</Button>
              </Space>
              <Space wrap>
                <Input placeholder="自定义动作名称" value={customName} onChange={(e) => setCustomName(e.target.value)} style={{ width: 180 }} />
                <InputNumber size="small" min={1} max={20} value={customSets} onChange={(v) => setCustomSets(v ?? 3)} style={{ width: 70 }} addonBefore="组" />
                <InputNumber size="small" min={1} max={100} value={customReps} onChange={(v) => setCustomReps(v ?? 10)} style={{ width: 70 }} addonBefore="次" />
              </Space>
              {selectedExercises.length > 0 && (
                <Space wrap>
                  {selectedExercises.map((sel, idx) => {
                    const exName = sel.customName || `#${sel.exerciseId}`
                    return (
                      <Tag
                        key={`${sel.exerciseId || sel.customName}-${idx}`}
                        closable
                        onClose={() => setSelectedExercises((prev) => prev.filter((_, i) => i !== idx))}
                      >
                        {exName} · {sel.sets ?? 3}组×{sel.reps ?? 10}次{sel.weight ? ` · ${sel.weight}kg` : ''}
                        {sel.customName && <Tag color="default" style={{ marginLeft: 4 }}>自定义</Tag>}
                      </Tag>
                    )
                  })}
                </Space>
              )}
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="完成训练" open={completeOpen} onCancel={() => { setCompleteOpen(false); completeForm.resetFields() }} onOk={handleCompletePlan} okText="提交" cancelText="取消" width={isMobile ? '100%' : undefined} style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}>
        <Form form={completeForm} layout="vertical" style={{ marginTop: 16 }} initialValues={{ completedDate: dayjs(), actualDuration: 60, caloriesBurned: 0 }}>
          <Form.Item name="actualDuration" label="实际时长" rules={[{ required: true }]}><InputNumber addonAfter="分钟" style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="caloriesBurned" label="消耗热量"><InputNumber addonAfter="kcal" style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="completedDate" label="完成日期"><DatePicker style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>

      <ExercisePicker
        open={exercisePickerOpen}
        onClose={() => setExercisePickerOpen(false)}
        onConfirm={(exercises) => { setSelectedExercises(exercises); setExercisePickerOpen(false) }}
        initialExercises={selectedExercises}
      />

      <ExercisePicker
        open={detailExercisePickerOpen}
        onClose={() => setDetailExercisePickerOpen(false)}
        onConfirm={(exercises) => handleAddExercisesToDetail(exercises)}
        initialExercises={[]}
      />

      <Modal
        title="计划详情"
        open={detailOpen}
        onCancel={() => { setDetailOpen(false); setDetailData(null); setEditingExerciseId(null); setEditingDraft(null) }}
        footer={null}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { top: 0, margin: 0, maxWidth: '100%' } : undefined}
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : detailData ? (
          <Space direction="vertical" style={{ width: '100%' }} size={16}>
            <div>
              <Typography.Title level={5} style={{ margin: '0 0 8px' }}>{detailData.planName}</Typography.Title>
              <Space wrap>
                {getTypeTag(detailData.planType)}
                {detailData.targetIntensity && getIntensityTag(detailData.targetIntensity)}
                <Tag>{detailData.estimatedDuration} 分钟</Tag>
                <Tag color={detailData.status === 'completed' ? '#10B981' : '#06B6D4'}>
                  {detailData.status === 'completed' ? '已完成' : '待完成'}
                </Tag>
              </Space>
            </div>
            {detailData.note && <Typography.Text type="secondary">{detailData.note}</Typography.Text>}
            {detailData.exercises.length > 0 ? (
              <List
                dataSource={detailData.exercises}
                renderItem={(ex: PlanExerciseItemOutput) => {
                  const isEditing = editingExerciseId === ex.id
                  return (
                    <>
                      <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar style={{ backgroundColor: '#F59E0B' }}>
                          <Dumbbell size={16} />
                        </Avatar>}
                        title={ex.customName || ex.nameCn || '自定义动作'}
                        description={
                          ex.exerciseId ? (
                          <div>
                            <Space wrap size={4}>
                              <Tag color="blue">{ex.targetMuscle}</Tag>
                              {ex.difficulty && <Tag>{ex.difficulty}</Tag>}
                              {ex.forceType && <Tag color="green">{ex.forceType}</Tag>}
                              {ex.mechanics && <Tag color="purple">{ex.mechanics}</Tag>}
                              {ex.equipment && <Tag color="orange">{ex.equipment}</Tag>}
                            </Space>
                            {ex.helperMuscles && (
                              <div style={{ fontSize: 12, color: '#999', marginTop: 4 }}>
                                辅助肌肉：{ex.helperMuscles}
                              </div>
                            )}
                          </div>
                          ) : (
                            <Tag color="default">自定义</Tag>
                          )
                        }
                      />
                      <div style={{ textAlign: 'right', flexShrink: 0 }}>
                        {!isEditing && (
                          <>
                            <Typography.Text strong>{ex.sets} 组 × {ex.reps} 次</Typography.Text>
                            {ex.weight && <Typography.Text type="secondary" style={{ display: 'block', fontSize: 12 }}>{ex.weight} kg</Typography.Text>}
                            <div>
                              <Button size="small" type="link" onClick={() => { setEditingExerciseId(ex.id); setEditingDraft({ sets: ex.sets, reps: ex.reps, weight: ex.weight ?? null }) }}>编辑</Button>
                              <Popconfirm title="确认删除" description="确定要删除该动作吗？" onConfirm={() => handleDeleteExerciseFromDetail(ex.id)} okText="删除" cancelText="取消" okButtonProps={{ danger: true }}>
                                <Button size="small" type="link" danger>删除</Button>
                              </Popconfirm>
                            </div>
                          </>
                        )}
                      </div>
                    </List.Item>
                    {isEditing && (
                      <List.Item style={{ display: 'block', padding: '12px 16px', background: '#FAFAFA', borderRadius: 8, marginBottom: 8, border: '1px solid #e8e8e8' }}>
                        <Row gutter={16} style={{ marginBottom: 12 }}>
                          <Col xs={8}>
                            <InputNumber
                              size="middle"
                              min={1}
                              max={20}
                              value={editingDraft?.sets ?? ex.sets}
                              onChange={v => setEditingDraft(prev => prev ? { ...prev, sets: v ?? prev.sets } : { sets: v ?? ex.sets, reps: ex.reps, weight: ex.weight ?? null })}
                              style={{ width: '100%', fontSize: 16, height: 40 }}
                              addonBefore="组"
                            />
                          </Col>
                          <Col xs={8}>
                            <InputNumber
                              size="middle"
                              min={1}
                              max={100}
                              value={editingDraft?.reps ?? ex.reps}
                              onChange={v => setEditingDraft(prev => prev ? { ...prev, reps: v ?? prev.reps } : { sets: ex.sets, reps: v ?? ex.reps, weight: ex.weight ?? null })}
                              style={{ width: '100%', fontSize: 16, height: 40 }}
                              addonBefore="次"
                            />
                          </Col>
                          <Col xs={8}>
                            <InputNumber
                              size="middle"
                              min={0}
                              max={500}
                              step={0.5}
                              value={editingDraft?.weight ?? ex.weight ?? undefined}
                              onChange={v => setEditingDraft(prev => prev ? { ...prev, weight: v } : { sets: ex.sets, reps: ex.reps, weight: v })}
                              style={{ width: '100%', fontSize: 16, height: 40 }}
                              addonBefore="kg"
                              placeholder="-"
                            />
                          </Col>
                        </Row>
                        <Space>
                          <Button type="primary" onClick={async () => {
                            const draft = editingDraft ?? { sets: ex.sets, reps: ex.reps, weight: ex.weight ?? null }
                            try {
                              await trainingApi.updatePlanExercise(ex.id, { sets: draft.sets, reps: draft.reps, weight: draft.weight ?? undefined })
                              // 保存成功后写回 detailData
                              setDetailData(prev => {
                                if (!prev) return prev
                                return { ...prev, exercises: prev.exercises.map(e => e.id === ex.id ? { ...e, sets: draft.sets, reps: draft.reps, weight: draft.weight } : e) }
                              })
                              message.success('更新成功')
                              setEditingExerciseId(null)
                              setEditingDraft(null)
                            } catch { message.error('更新失败') }
                          }}>保存</Button>
                          <Button onClick={() => { setEditingExerciseId(null); setEditingDraft(null) }}>取消</Button>
                        </Space>
                      </List.Item>
                    )}
                    </>
                  )
                }}
              />
            ) : (
              <Typography.Text type="secondary">暂无训练动作</Typography.Text>
            )}
            {detailData.status !== 'completed' && (
              <div style={{ padding: '12px 0', borderTop: '1px dashed #e8e8e8' }}>
                <Typography.Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>添加动作</Typography.Text>
                <Space direction="vertical" style={{ width: '100%' }} size={8}>
                  <Space wrap>
                    <Button icon={<PlusOutlined />} onClick={() => setDetailExercisePickerOpen(true)}>从动作库选择</Button>
                    <Button type="dashed" icon={<PlusOutlined />} onClick={handleAddCustomExerciseToDetail}>添加自定义</Button>
                  </Space>
                  <Space wrap>
                    <Input placeholder="自定义动作名称" value={detailCustomName} onChange={(e) => setDetailCustomName(e.target.value)} style={{ width: 180 }} />
                    <InputNumber size="small" min={1} max={20} value={detailCustomSets} onChange={(v) => setDetailCustomSets(v ?? 3)} style={{ width: 70 }} addonBefore="组" />
                    <InputNumber size="small" min={1} max={100} value={detailCustomReps} onChange={(v) => setDetailCustomReps(v ?? 10)} style={{ width: 70 }} addonBefore="次" />
                  </Space>
                </Space>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: 8, marginTop: 8, borderTop: '1px solid #f0f0f0' }}>
              <Button onClick={() => { setDetailOpen(false); setDetailData(null); setEditingExerciseId(null); setEditingDraft(null) }}>关闭</Button>
              <Space>
                {detailPlanInfo?.isRecurring && detailPlanInfo?.isLastInGroup && (
                  <Button type="primary" icon={<SyncOutlined />} onClick={() => { handleRenewPlan(detailData!.planId); setDetailOpen(false) }}>
                    续期
                  </Button>
                )}
                <Button danger onClick={() => { if (detailData) handleDeletePlan(detailData.planId); setDetailOpen(false) }}>删除</Button>
              </Space>
            </div>
          </Space>
        ) : null}
      </Modal>
    </div>
  )
}

export default Training
