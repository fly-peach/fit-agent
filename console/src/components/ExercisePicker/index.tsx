import { useState, useEffect, useCallback } from 'react'
import { Modal, Input, Select, List, Card, Tag, Button, Space, Spin, InputNumber, Tabs, message, Collapse, Typography } from 'antd'
import { SearchOutlined, MinusOutlined, StarFilled, StarOutlined, EyeOutlined } from '@ant-design/icons'
import { exerciseApi, ExerciseItem, PinnedExercise, PlanExerciseInput } from '../../services/exercise'

const { Option } = Select
const { Text } = Typography

interface ExercisePickerProps {
  open: boolean
  onClose: () => void
  onConfirm: (exercises: PlanExerciseInput[]) => void
  initialExercises?: PlanExerciseInput[]
}

const DIFFICULTIES = ['初级', '中级', '专家级']

export default function ExercisePicker({ open, onClose, onConfirm, initialExercises = [] }: ExercisePickerProps) {
  const isMobile = window.innerWidth < 768

  const [activeTab, setActiveTab] = useState('library')

  // Library state
  const [keyword, setKeyword] = useState('')
  const [filters, setFilters] = useState<{ targetMuscle?: string; exerciseType?: string; difficulty?: string; equipment?: string; forceType?: string; mechanics?: string }>({})
  const [exerciseList, setExerciseList] = useState<ExerciseItem[]>([])
  const [loading, setLoading] = useState(false)
  const [categories, setCategories] = useState<{ muscles: string[]; types: string[]; equipment: string[]; forceTypes: string[]; mechanics: string[] }>({
    muscles: [],
    types: [],
    equipment: [],
    forceTypes: [],
    mechanics: [],
  })

  // Pinned state
  const [pinnedList, setPinnedList] = useState<PinnedExercise[]>([])
  const [pinnedLoading, setPinnedLoading] = useState(false)

  // Detail modal
  const [detailOpen, setDetailOpen] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detail, setDetail] = useState<{
    exerciseId?: number
    nameCn: string
    nameEn: string | null
    difficulty: string | null
    forceType: string | null
    mechanics: string | null
    equipment: string | null
    exerciseType: string | null
    targetMuscle: string
    helperMuscles: string
    instructions: string[]
    isPinned: boolean
  } | null>(null)

  // Selected exercises (for adding to plan)
  const [selected, setSelected] = useState<PlanExerciseInput[]>(initialExercises)

  // Load categories on mount
  useEffect(() => {
    if (!open) return
    Promise.all([
      exerciseApi.getMuscleCategories(),
      exerciseApi.getTypeCategories(),
      exerciseApi.getEquipmentCategories(),
      exerciseApi.getForceTypeCategories(),
      exerciseApi.getMechanicsCategories(),
    ]).then(([muscles, types, equipment, forceTypes, mechanics]) => {
      setCategories({ muscles, types, equipment, forceTypes, mechanics })
    })
  }, [open])

  // Load exercises from library
  const fetchExercises = useCallback(() => {
    setLoading(true)
    exerciseApi
      .listExercises({
        keyword: keyword || undefined,
        targetMuscle: filters.targetMuscle,
        exerciseType: filters.exerciseType,
        difficulty: filters.difficulty,
        equipment: filters.equipment,
        forceType: filters.forceType,
        mechanics: filters.mechanics,
        limit: 200,
      })
      .then((list) => setExerciseList(list))
      .finally(() => setLoading(false))
  }, [keyword, filters])

  useEffect(() => {
    if (!open || activeTab !== 'library') return
    fetchExercises()
  }, [open, activeTab, keyword, filters.targetMuscle, filters.exerciseType, filters.difficulty, filters.equipment, filters.forceType, filters.mechanics, fetchExercises])

  // Load pinned exercises
  useEffect(() => {
    if (!open || activeTab !== 'pinned') return
    setPinnedLoading(true)
    exerciseApi.getPinnedExercises()
      .then((list) => setPinnedList(list))
      .finally(() => setPinnedLoading(false))
  }, [open, activeTab])

  const isSelected = (exerciseId: number) => selected.some((e) => e.exerciseId === exerciseId)

  const addExercise = (exerciseId: number) => {
    if (isSelected(exerciseId)) return
    setSelected((prev) => [...prev, { exerciseId, sets: 3, reps: 10 }])
  }

  const removeExercise = (exerciseId: number) => {
    setSelected((prev) => prev.filter((e) => e.exerciseId !== exerciseId))
  }

  const updateSelected = (exerciseId: number, field: keyof PlanExerciseInput, value: number | string | undefined) => {
    setSelected((prev) => prev.map((e) => (e.exerciseId === exerciseId ? { ...e, [field]: value } : e)))
  }

  const handlePinToggle = async (exerciseId: number) => {
    const isPinned = exerciseList.some((e) => e.exerciseId === exerciseId && e.isPinned)
    try {
      if (isPinned) {
        await exerciseApi.unpinExercise(exerciseId)
        setExerciseList((prev) => prev.map((e) => e.exerciseId === exerciseId ? { ...e, isPinned: false } : e))
        setPinnedList((prev) => prev.filter((x) => x.exerciseId !== exerciseId))
      } else {
        await exerciseApi.pinExercise(exerciseId)
        setExerciseList((prev) => prev.map((e) => e.exerciseId === exerciseId ? { ...e, isPinned: true } : e))
      }
    } catch {
      message.error('操作失败')
    }
  }

  const openDetail = async (exerciseId: number) => {
    setDetailLoading(true)
    setDetailOpen(true)
    try {
      const data = await exerciseApi.getExerciseDetail(exerciseId)
      const isPinned = exerciseList.some((e) => e.exerciseId === exerciseId && e.isPinned)
        || pinnedList.some((p) => p.exerciseId === exerciseId)
      setDetail({
        exerciseId: data.exerciseId,
        nameCn: data.nameCn,
        nameEn: data.nameEn,
        difficulty: data.difficulty,
        forceType: data.forceType,
        mechanics: data.mechanics,
        equipment: data.equipment,
        exerciseType: data.exerciseType,
        targetMuscle: data.targetMuscle,
        helperMuscles: data.helperMuscles,
        instructions: data.instructions,
        isPinned,
      })
    } catch {
      message.error('获取动作详情失败')
    } finally {
      setDetailLoading(false)
    }
  }

  const handleDetailPinToggle = async () => {
    if (!detail) return
    const exerciseId = detail.exerciseId
      ?? exerciseList.find((e) => e.nameCn === detail.nameCn)?.exerciseId
      ?? pinnedList.find((p) => p.nameCn === detail.nameCn)?.exerciseId
    if (exerciseId == null) return
    try {
      if (detail.isPinned) {
        await exerciseApi.unpinExercise(exerciseId)
        setDetail({ ...detail, isPinned: false })
        setExerciseList((prev) => prev.map((e) => e.exerciseId === exerciseId ? { ...e, isPinned: false } : e))
        setPinnedList((prev) => prev.filter((x) => x.exerciseId !== exerciseId))
      } else {
        await exerciseApi.pinExercise(exerciseId)
        setDetail({ ...detail, isPinned: true })
        setExerciseList((prev) => prev.map((e) => e.exerciseId === exerciseId ? { ...e, isPinned: true } : e))
      }
    } catch {
      message.error('操作失败')
    }
  }

  const handleConfirm = () => {
    onConfirm(selected)
    setSelected([])
    setKeyword('')
    setFilters({})
  }

  const handleCancel = () => {
    setSelected([])
    onClose()
  }

  const modalStyle: React.CSSProperties = isMobile
    ? { top: 0, margin: 0, maxWidth: '100%', height: '100vh', display: 'flex', flexDirection: 'column' }
    : { top: 20, maxWidth: 900 }

  const renderExerciseCard = (item: ExerciseItem) => {
    const selected_ = isSelected(item.exerciseId)
    return (
    <Card
      key={item.exerciseId}
      size="small"
      hoverable
      style={{
        width: '100%',
        borderColor: selected_ ? '#52c41a' : undefined,
        borderWidth: selected_ ? 2 : 1,
      }}
      onClick={() => openDetail(item.exerciseId)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{item.nameCn}</div>
          {item.nameEn && (
            <div style={{ fontSize: 12, color: '#999', marginBottom: 6 }}>{item.nameEn}</div>
          )}
          <Space wrap size={4}>
            <Tag color="blue">{item.targetMuscle}</Tag>
            {item.difficulty && <Tag>{item.difficulty}</Tag>}
            {item.forceType && <Tag color="green">{item.forceType}</Tag>}
            {item.mechanics && <Tag color="purple">{item.mechanics}</Tag>}
            {item.equipment && <Tag color="orange">{item.equipment}</Tag>}
          </Space>
        </div>
        <Space direction="vertical" align="end" size={4}>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={(e) => { e.stopPropagation(); openDetail(item.exerciseId) }}
          />
          {renderStar(item.exerciseId, item.isPinned)}
          {!selected_ && (
            <Button type="link" size="small" onClick={(e) => { e.stopPropagation(); addExercise(item.exerciseId) }}>
              添加
            </Button>
          )}
          {selected_ && (
            <Tag color="green" style={{ margin: 0 }}>已添加</Tag>
          )}
        </Space>
      </div>
    </Card>
    )
  }

  const renderPinnedCard = (item: PinnedExercise) => {
    const selected_ = isSelected(item.exerciseId)
    return (
    <Card
      key={item.exerciseId}
      size="small"
      hoverable
      style={{
        width: '100%',
        borderColor: selected_ ? '#52c41a' : undefined,
        borderWidth: selected_ ? 2 : 1,
      }}
      onClick={() => openDetail(item.exerciseId)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
            <StarFilled style={{ color: '#F59E0B', marginRight: 4, fontSize: 12 }} />
            {item.nameCn}
          </div>
          {item.nameEn && (
            <div style={{ fontSize: 12, color: '#999', marginBottom: 6 }}>{item.nameEn}</div>
          )}
          <Space wrap size={4}>
            <Tag color="blue">{item.targetMuscle}</Tag>
            {item.difficulty && <Tag>{item.difficulty}</Tag>}
            {item.forceType && <Tag color="green">{item.forceType}</Tag>}
            {item.mechanics && <Tag color="purple">{item.mechanics}</Tag>}
            {item.equipment && <Tag color="orange">{item.equipment}</Tag>}
          </Space>
        </div>
        <Space direction="vertical" align="end" size={4}>
          <Button
            type="text"
            size="small"
            icon={<EyeOutlined />}
            onClick={(e) => { e.stopPropagation(); openDetail(item.exerciseId) }}
          />
          {!selected_ && (
            <Button type="link" size="small" onClick={(e) => { e.stopPropagation(); addExercise(item.exerciseId) }}>
              添加
            </Button>
          )}
          {selected_ && (
            <Tag color="green" style={{ margin: 0 }}>已添加</Tag>
          )}
        </Space>
      </div>
    </Card>
    )
  }

  const renderStar = (exerciseId: number, isPinned: boolean) => (
    <Button
      type="text"
      size="small"
      icon={isPinned ? <StarFilled style={{ color: '#F59E0B' }} /> : <StarOutlined />}
      onClick={(e) => { e.stopPropagation(); handlePinToggle(exerciseId) }}
      style={{ padding: '0 4px', fontSize: 16 }}
    />
  )

  const tabItems = [
    {
      key: 'library',
      label: '动作库',
      children: (
        <>
          <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }} size={12}>
            <Input.Search
              placeholder="搜索动作名称"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              onSearch={fetchExercises}
              prefix={<SearchOutlined />}
              allowClear
            />
            <Space wrap>
              <Select
                placeholder="目标肌肉"
                allowClear
                style={{ width: isMobile ? '100%' : 150 }}
                value={filters.targetMuscle}
                onChange={(v) => setFilters((f) => ({ ...f, targetMuscle: v }))}
              >
                {categories.muscles.map((m) => (
                  <Option key={m} value={m}>{m}</Option>
                ))}
              </Select>
              <Select
                placeholder="动作类型"
                allowClear
                style={{ width: isMobile ? '100%' : 150 }}
                value={filters.exerciseType}
                onChange={(v) => setFilters((f) => ({ ...f, exerciseType: v }))}
              >
                {categories.types.map((t) => (
                  <Option key={t} value={t}>{t}</Option>
                ))}
              </Select>
              <Select
                placeholder="难度"
                allowClear
                style={{ width: isMobile ? '100%' : 120 }}
                value={filters.difficulty}
                onChange={(v) => setFilters((f) => ({ ...f, difficulty: v }))}
              >
                {DIFFICULTIES.map((d) => (
                  <Option key={d} value={d}>{d}</Option>
                ))}
              </Select>
              <Select
                placeholder="器械"
                allowClear
                style={{ width: isMobile ? '100%' : 150 }}
                value={filters.equipment}
                onChange={(v) => setFilters((f) => ({ ...f, equipment: v }))}
              >
                {categories.equipment.map((eq) => (
                  <Option key={eq} value={eq}>{eq}</Option>
                ))}
              </Select>
              <Select
                placeholder="发力类型"
                allowClear
                style={{ width: isMobile ? '100%' : 120 }}
                value={filters.forceType}
                onChange={(v) => setFilters((f) => ({ ...f, forceType: v }))}
              >
                {categories.forceTypes.map((ft) => (
                  <Option key={ft} value={ft}>{ft}</Option>
                ))}
              </Select>
              <Select
                placeholder="力学类型"
                allowClear
                style={{ width: isMobile ? '100%' : 120 }}
                value={filters.mechanics}
                onChange={(v) => setFilters((f) => ({ ...f, mechanics: v }))}
              >
                {categories.mechanics.map((m) => (
                  <Option key={m} value={m}>{m}</Option>
                ))}
              </Select>
            </Space>
          </Space>

          <Spin spinning={loading}>
            <List
              grid={isMobile ? undefined : { gutter: 12, column: 2 }}
              dataSource={exerciseList}
              renderItem={(item) => <List.Item>{renderExerciseCard(item)}</List.Item>}
              locale={{ emptyText: '暂无匹配的动作' }}
            />
          </Spin>
        </>
      ),
    },
    {
      key: 'pinned',
      label: '我的收藏',
      children: (
        <Spin spinning={pinnedLoading}>
          {pinnedList.length > 0 ? (
            <List
              grid={isMobile ? undefined : { gutter: 12, column: 2 }}
              dataSource={pinnedList}
              renderItem={(item) => <List.Item>{renderPinnedCard(item)}</List.Item>}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
              暂无收藏动作，在动作库中点击星标收藏
            </div>
          )}
        </Spin>
      ),
    },
  ]

  return (
    <>
    <Modal
      title="选择训练动作"
      open={open}
      onCancel={handleCancel}
      onOk={handleConfirm}
      okText={`确认（已选 ${selected.length} 个动作）`}
      cancelText="取消"
      width={900}
      style={modalStyle}
      styles={{ body: { maxHeight: isMobile ? 'calc(100vh - 120px)' : 600, overflow: 'auto' } }}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />

      {/* Selected Exercises — edit sets/reps/weight/duration here */}
      {selected.length > 0 && (
        <div style={{ marginTop: 16, padding: '12px 16px', background: '#f5f5f5', borderRadius: 8 }}>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>已选 {selected.length} 个动作</div>
          <Space direction="vertical" style={{ width: '100%' }} size={8}>
            {selected.map((sel) => {
              const exerciseId = sel.exerciseId!
              const ex = exerciseList.find((e) => e.exerciseId === exerciseId) || pinnedList.find((p) => p.exerciseId === exerciseId)
              return (
                <div key={exerciseId} style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <Button type="link" size="small" onClick={() => openDetail(exerciseId)} style={{ fontWeight: 500, minWidth: 80, padding: 0 }}>
                    {ex?.nameCn || `#${exerciseId}`}
                  </Button>
                  <Text type="secondary" style={{ fontSize: 12 }}>组</Text>
                  <InputNumber
                    size="small"
                    min={1}
                    max={20}
                    value={sel.sets ?? 3}
                    onChange={(v) => updateSelected(exerciseId, 'sets', v ?? 3)}
                    style={{ width: 60 }}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>次</Text>
                  <InputNumber
                    size="small"
                    min={1}
                    max={100}
                    value={sel.reps ?? 10}
                    onChange={(v) => updateSelected(exerciseId, 'reps', v ?? 10)}
                    style={{ width: 60 }}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>kg</Text>
                  <InputNumber
                    size="small"
                    min={0}
                    step={2.5}
                    value={sel.weight}
                    placeholder="重量"
                    onChange={(v) => updateSelected(exerciseId, 'weight', v ?? undefined)}
                    style={{ width: 70 }}
                  />
                  <Text type="secondary" style={{ fontSize: 12 }}>时(s)</Text>
                  <InputNumber
                    size="small"
                    min={0}
                    step={10}
                    value={sel.duration}
                    placeholder="时间"
                    onChange={(v) => updateSelected(exerciseId, 'duration', v ?? undefined)}
                    style={{ width: 70 }}
                  />
                  <Button
                    size="small"
                    type="text"
                    danger
                    icon={<MinusOutlined />}
                    onClick={() => removeExercise(exerciseId)}
                  />
                </div>
              )
            })}
          </Space>
        </div>
      )}
    </Modal>

    {/* Exercise Detail Modal */}
    <Modal
      title={detail?.nameCn || '动作详情'}
      open={detailOpen}
      onCancel={() => { setDetailOpen(false); setDetail(null) }}
      footer={null}
      width={isMobile ? '100%' : 700}
    >
      <Spin spinning={detailLoading}>
        {detail && (
          <Space direction="vertical" style={{ width: '100%' }} size={16}>
            <Space wrap>
              <Tag color="blue">目标肌肉: {detail.targetMuscle}</Tag>
              {detail.helperMuscles && <Tag color="cyan">辅助肌肉: {detail.helperMuscles}</Tag>}
              {detail.difficulty && <Tag>{detail.difficulty}</Tag>}
              {detail.forceType && <Tag color="green">{detail.forceType}</Tag>}
              {detail.mechanics && <Tag color="purple">{detail.mechanics}</Tag>}
              {detail.equipment && <Tag color="orange">{detail.equipment}</Tag>}
              {detail.exerciseType && <Tag color="magenta">{detail.exerciseType}</Tag>}
              <Button
                type="text"
                size="small"
                icon={detail.isPinned ? <StarFilled style={{ color: '#F59E0B' }} /> : <StarOutlined />}
                onClick={handleDetailPinToggle}
              >
                {detail.isPinned ? '已收藏' : '收藏'}
              </Button>
              {detail.exerciseId != null && (
                <Button
                  type={isSelected(detail.exerciseId) ? 'default' : 'primary'}
                  size="small"
                  onClick={() => { addExercise(detail.exerciseId!) }}
                >
                  {isSelected(detail.exerciseId) ? '已添加' : '添加'}
                </Button>
              )}
            </Space>

            {detail.nameEn && (
              <Text type="secondary" style={{ fontSize: 13 }}>{detail.nameEn}</Text>
            )}

            <Collapse
              defaultActiveKey={['instructions']}
              items={[{
                key: 'instructions',
                label: <Text strong>动作要领 ({detail.instructions.length} 步)</Text>,
                children: (
                  <ol style={{ margin: 0, paddingLeft: 20 }}>
                    {detail.instructions.map((step, i) => (
                      <li key={i} style={{ marginBottom: 6, lineHeight: 1.6 }}>{step}</li>
                    ))}
                  </ol>
                ),
              }]}
            />
          </Space>
        )}
      </Spin>
    </Modal>
    </>
  )
}
