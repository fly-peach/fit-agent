import React, { useEffect, useState } from 'react'
import { Card, Typography, Form, Input, Button, message, Space, Tag, Select, Row, Col, Alert, Modal, Table, Statistic, Spin, Popconfirm } from 'antd'
import { Bot, Key, Cpu, Sparkles, FolderOpen, CheckCircle2 } from 'lucide-react'
import { EyeOutlined, ReloadOutlined, DeleteOutlined, ExperimentOutlined } from '@ant-design/icons'
import { agentApi, workspaceApi, type AgentWorkspaceStatus } from '../../services/user'
import { contextApi, ContextStats, CacheEntry } from '../../services/context'

const modelOptions = [
  { value: 'qwen-turbo', label: 'Qwen Turbo (快速，推荐)', recommended: true },
  { value: 'qwen-plus', label: 'Qwen Plus (均衡)' },
  { value: 'qwen-max', label: 'Qwen Max (强大)' },
  { value: 'qwen-max-longcontext', label: 'Qwen Max LongContext (长文本)' },
  { value: 'qwen2.5-72b-instruct', label: 'Qwen2.5 72B (最强)' },
  { value: 'qwen2.5-32b-instruct', label: 'Qwen2.5 32B' },
  { value: 'qwen2.5-14b-instruct', label: 'Qwen2.5 14B' },
  { value: 'qwen2.5-7b-instruct', label: 'Qwen2.5 7B (轻量)' },
  { value: 'qwen-vl-max', label: 'Qwen2.5-VL Max (视觉理解最强)' },
  { value: 'qwen-vl-plus', label: 'Qwen2.5-VL Plus (视觉理解均衡)' },
  { value: 'qwen2.5-vl-72b', label: 'Qwen2.5-VL 72B (开源视觉理解)' },
  { value: 'qwen2.5-vl-32b', label: 'Qwen2.5-VL 32B (视觉性价比)' },
  { value: 'qwen2.5-vl-7b', label: 'Qwen2.5-VL 7B (视觉轻量)' },
  { value: 'qwen3-vl-plus', label: 'Qwen3-VL Plus (新一代视觉)' },
  { value: 'qwen3-vl-flash', label: 'Qwen3-VL Flash (新一代视觉快速)' },
]

// ---------------------------------------------------------------------------
// 智能体人格预设
// ---------------------------------------------------------------------------

interface PersonalityPreset {
  key: string
  label: string
  emoji: string
  description: string
  agents_md: string
  soul_md: string
}

const personalityPresets: PersonalityPreset[] = [
  {
    key: 'rogers_default',
    label: 'Rogers · 专业教练',
    emoji: '🏋️',
    description: '专业、耐心、温暖的健身教练，鼓励式陪伴训练',
    agents_md: `你是 Rogers，一个专业的健身和健康管理助手。

## 职责

- 帮助用户制定训练计划
- 记录饮食和营养摄入
- 跟踪健康指标和趋势
- 提供专业、温暖的健康建议

## 行为准则

- 使用你拥有的工具来读取和更新用户的数据
- 如果用户没有登录，提示他们先登录
- 如果数据不存在，返回友好的提示而不是错误
- 用中文回答`,
    soul_md: `你是一个专业、耐心、温暖的健身教练。你关心用户的健康，
会用鼓励性的语言帮助用户坚持训练和健康饮食。
你尊重每个用户的个体差异，提供个性化的建议。`,
  },
  {
    key: 'captain_rogers',
    label: '史蒂夫·罗杰斯',
    emoji: '🛡️',
    description: '美国队长风格，坚定、鼓舞、领导力满满',
    agents_md: `你是 Steve，一位退役老兵转行的健身教练。你经历过战场上最严酷的考验，现在用同样的纪律和决心帮助人们变得更强。

## 职责

- 用军事化的纪律帮助用户建立训练习惯
- 制定循序渐进的力量和体能训练计划
- 记录饮食和营养摄入
- 跟踪健康指标和趋势

## 行为准则

- 你的风格坚定而鼓舞人心，像一位值得信任的战友
- 使用你拥有的工具来读取和更新用户的数据
- 如果用户没有登录，提示他们先登录
- 如果数据不存在，返回友好的提示而不是错误
- 用中文回答`,
    soul_md: `你是一位经历过战火的老兵，深知纪律和坚持的力量。你的语气坚定、正直、充满鼓励。你不会让任何人轻易放弃——因为你知道每个人体内都蕴藏着比自己想象的更强大的力量。你用"士兵"或"战友"称呼用户，用简短有力的话语激发他们的斗志。你相信：没有做不到的事，只有不想做的事。`,
  },
  {
    key: 'onee_sama',
    label: '御姐教练',
    emoji: '👑',
    description: '成熟、自信、带点毒舌但真心的健身御姐',
    agents_md: `你是姐姐，一个专业又有魅力的健身教练。你用成熟女性的视角帮助用户变得更自信、更有魅力。

## 职责

- 帮助用户制定适合的训练计划，特别关注体态和气质
- 记录饮食和营养摄入
- 跟踪健康指标和趋势
- 提供关于穿搭、护肤和自信心的综合建议

## 行为准则

- 你是一位成熟自信的姐姐，说话直接但不失温柔
- 使用你拥有的工具来读取和更新用户的数据
- 如果用户没有登录，提示他们先登录
- 如果数据不存在，返回友好的提示而不是错误
- 用中文回答`,
    soul_md: `你是一位成熟、自信、有魅力的姐姐型教练。你说话直接，偶尔带点毒舌，但每一句话都是真心为对方好。你喜欢用"小朋友"称呼用户，会用温柔的语气说严厉的话。你知道什么是真正的美，不是瘦就是好，而是健康、自信和由内而外的光彩。你相信每个人都有潜力变得更好，而你的任务就是帮他们找到那个最好的自己。`,
  },
  {
    key: 'strict_coach',
    label: '铁血教官',
    emoji: '⚡',
    description: '严格、高效、数据驱动的铁血教官风格',
    agents_md: `你是教官，一个高效、严格的健身训练系统。你用数据说话，用最直接的方式推动进步。

## 职责

- 制定科学、高效的训练计划
- 严格记录饮食和营养摄入
- 跟踪和分析健康指标数据
- 基于数据反馈调整训练方案

## 行为准则

- 你的风格严格、直接、以结果为导向
- 使用你拥有的工具来读取和更新用户的数据
- 如果用户没有登录，提示他们先登录
- 如果数据不存在，返回友好的提示而不是错误
- 用中文回答`,
    soul_md: `你是一位严格的铁血教官。你不说废话，只给干货。你相信数据胜于雄辩，行动胜于承诺。你说话简短、有力、直接。你不会因为用户的借口而妥协，但你会在他们真正努力的时候给予认可。你相信纪律是通往自由唯一的道路。`,
  },
  {
    key: 'buddy',
    label: '健身搭子',
    emoji: '🤝',
    description: '像朋友一样的健身搭子，轻松有趣',
    agents_md: `你是你的健身搭子，一个和你一起打卡、一起流汗、一起吃健康餐的好朋友。

## 职责

- 一起制定有趣的训练计划
- 互相监督饮食和营养摄入
- 一起跟踪健康指标和趋势
- 分享健身心得和生活经验

## 行为准则

- 你像最好的朋友一样和用户聊天，轻松、幽默、接地气
- 使用你拥有的工具来读取和更新用户的数据
- 如果用户没有登录，提示他们先登录
- 如果数据不存在，返回友好的提示而不是错误
- 用中文回答`,
    soul_md: `你是用户最好的健身搭子。你说话轻松幽默，喜欢用网络用语和表情。你会和用户一起"打卡"，一起吐槽健身的痛苦，也会在对方想要放弃的时候用最好的方式鼓励。你不会说教，而是像一个真正的朋友一样，用自己的经验和建议帮助对方。你知道健身最重要的是坚持，而坚持的前提是——开心。`,
  },
  {
    key: 'custom',
    label: '自定义人格',
    emoji: '✏️',
    description: '完全自定义你的智能体人格',
    agents_md: '',
    soul_md: '',
  },
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

const AgentConfig: React.FC = () => {
  const [agentForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [apiKeyMasked, setApiKeyMasked] = useState('')
  const [useCustomModel, setUseCustomModel] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<string>('')
  const [hasApiKeyInput, setHasApiKeyInput] = useState(false)

  const [savingModel, setSavingModel] = useState(false)
  const isMobile = useIsMobile()

  // 工作目录状态
  const [workspaceStatus, setWorkspaceStatus] = useState<AgentWorkspaceStatus | null>(null)
  const [workspaceLoading, setWorkspaceLoading] = useState(false)
  const [workspaceSaving, setWorkspaceSaving] = useState(false)
  const [customWorkspacePath, setCustomWorkspacePath] = useState('')

  // 上下文管理状态
  const [contextStats, setContextStats] = useState<ContextStats | null>(null)
  const [cacheList, setCacheList] = useState<CacheEntry[]>([])
  const [contextLoading, setContextLoading] = useState(false)
  const [compactLoading, setCompactLoading] = useState(false)
  const [cacheContent, setCacheContent] = useState<string | null>(null)
  const [cacheModalVisible, setCacheModalVisible] = useState(false)

  const fetchWorkspaceStatus = async () => {
    setWorkspaceLoading(true)
    try {
      const status = await workspaceApi.getStatus()
      setWorkspaceStatus(status)
      if (status.local_working_dir) {
        setCustomWorkspacePath(status.local_working_dir)
      }
    } catch {
      // 忽略错误
    } finally {
      setWorkspaceLoading(false)
    }
  }

  const handleCreateWorkspace = async (useCustomPath: boolean = false) => {
    setWorkspaceSaving(true)
    try {
      const data = useCustomPath && customWorkspacePath
        ? { local_working_dir: customWorkspacePath }
        : {}
      await workspaceApi.createOrUpdate(data)
      message.success('工作目录配置成功！')
      await fetchWorkspaceStatus()
    } catch (e: any) {
      message.error(e?.detail || '配置失败，请检查路径')
    } finally {
      setWorkspaceSaving(false)
    }
  }

  const fetchContextData = async () => {
    setContextLoading(true)
    try {
      const [statsData, cacheData] = await Promise.all([
        contextApi.getStats(),
        contextApi.listCache(),
      ])
      setContextStats(statsData)
      setCacheList(cacheData)
    } catch {
      message.error('获取上下文数据失败')
    } finally {
      setContextLoading(false)
    }
  }

  const handleClearCache = async () => {
    try {
      const result = await contextApi.clearCache()
      message.success(`已清理 ${result.cleared} 个缓存文件`)
      fetchContextData()
    } catch {
      message.error('清理失败')
    }
  }

  const handleCompact = async () => {
    setCompactLoading(true)
    try {
      const result = await contextApi.triggerCompact()
      if (result.success) {
        message.success('上下文压缩完成')
      } else {
        message.warning(`压缩未生效: ${result.reason}`)
      }
      fetchContextData()
    } catch {
      message.error('压缩失败')
    } finally {
      setCompactLoading(false)
    }
  }

  const handleViewCache = async (id: string) => {
    try {
      const data = await contextApi.getCache(id)
      setCacheContent(data.content)
      setCacheModalVisible(true)
    } catch {
      message.error('获取缓存失败')
    }
  }

  useEffect(() => {
    fetchConfig()
    fetchWorkspaceStatus()
    fetchContextData()
  }, [])

  const fetchConfig = async () => {
    try {
      const data = await agentApi.getConfig()
      agentForm.setFieldsValue({
        agents_md: data.agents_md,
        soul_md: data.soul_md,
        api_key: '',
        model_name: data.model_name,
      })
      const isPreset = modelOptions.some(opt => opt.value === data.model_name)
      setUseCustomModel(!isPreset)
      const matchedPreset = personalityPresets.find(
        p => p.key !== 'custom' && p.agents_md === data.agents_md && p.soul_md === data.soul_md,
      )
      setSelectedPreset(matchedPreset ? matchedPreset.key : (data.agents_md || data.soul_md ? 'custom' : 'rogers_default'))
      setApiKeyMasked(data.api_key_masked)
      setHasApiKeyInput(false)
    } catch {
      // 配置未找到时使用默认值，引导用户完成首次配置
      agentForm.setFieldsValue({
        agents_md: personalityPresets[0].agents_md,
        soul_md: personalityPresets[0].soul_md,
        api_key: '',
        model_name: 'qwen-turbo',
      })
      setSelectedPreset('rogers_default')
      setUseCustomModel(false)
      setApiKeyMasked('')
      setHasApiKeyInput(false)
      message.info('首次使用，请配置 DashScope API Key 后保存即可开始使用')
    }
  }
  const handleSaveModel = async () => {
    try {
      setSavingModel(true)
      const values = agentForm.getFieldsValue(['api_key', 'model_name'])
      // 如果用户没有输入新的 api_key，不传这个字段，避免覆盖
      const payload: any = { model_name: values.model_name }
      if (hasApiKeyInput && values.api_key) {
        payload.api_key = values.api_key
      } else if (hasApiKeyInput && !values.api_key) {
        // 用户清空了输入，表示要清除自定义 api_key
        payload.api_key = ''
      }
      await agentApi.updateConfig(payload)
      message.success('模型配置已保存')
      fetchConfig()
    } catch {
      message.error('保存失败')
    } finally {
      setSavingModel(false)
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const values = await agentForm.validateFields()
      // 如果用户没有输入新的 api_key，不传这个字段，避免覆盖
      const payload: any = {
        agents_md: values.agents_md,
        soul_md: values.soul_md,
        model_name: values.model_name,
      }
      if (hasApiKeyInput && values.api_key) {
        payload.api_key = values.api_key
      } else if (hasApiKeyInput && !values.api_key) {
        // 用户清空了输入，表示要清除自定义 api_key
        payload.api_key = ''
      }
      await agentApi.updateConfig(payload)
      message.success('Agent 配置已保存')
      fetchConfig()
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  const handleApplyPersonality = (preset: PersonalityPreset) => {
    const currentAgents = agentForm.getFieldValue('agents_md')
    const currentSoul = agentForm.getFieldValue('soul_md')
    if ((currentAgents && currentAgents.trim()) || (currentSoul && currentSoul.trim())) {
      Modal.confirm({
        title: `应用「${preset.label}」人格`,
        content: '当前已有自定义内容，应用新的人格将覆盖原有内容，是否继续？',
        okText: '确认应用',
        okType: 'danger',
        cancelText: '取消',
        onOk: () => {
          agentForm.setFieldsValue({
            agents_md: preset.agents_md,
            soul_md: preset.soul_md,
          })
          setSelectedPreset(preset.key)
          message.success(`已应用「${preset.label}」人格`)
        },
      })
    } else {
      agentForm.setFieldsValue({
        agents_md: preset.agents_md,
        soul_md: preset.soul_md,
      })
      setSelectedPreset(preset.key)
      message.success(`已应用「${preset.label}」人格`)
    }
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: isMobile ? 12 : 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#F5F3FF', color: '#A78BFA' }}>
          <Bot size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>AI Agent 配置</Typography.Title>
      </div>

      <Form form={agentForm} layout="vertical" onFinish={handleSave}>
        <Space direction="vertical" size={isMobile ? 16 : 24} style={{ width: '100%' }}>
          {/* 工作目录配置卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <FolderOpen size={16} style={{ color: '#10B981' }} />
                <span>AI 工作目录</span>
              </div>
            }
            style={{ border: 'none' }}
          >
            <Spin spinning={workspaceLoading}>
              {workspaceStatus?.is_configured ? (
                <Alert
                  type="success"
                  showIcon
                  icon={<CheckCircle2 size={20} />}
                  message={
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span>
                        目录已配置
                        <Tag color="success" style={{ marginLeft: 8 }}>
                          就绪
                        </Tag>
                      </span>
                      <Button
                        type="text"
                        size="small"
                        onClick={() => Modal.confirm({
                          title: '更改工作目录',
                          content: (
                            <div style={{ marginTop: 16 }}>
                              <Typography.Text type="secondary">
                                当前目录：{workspaceStatus.local_working_dir}
                              </Typography.Text>
                              <Input
                                style={{ marginTop: 12 }}
                                placeholder="输入新的目录路径（留空使用默认）"
                                value={customWorkspacePath}
                                onChange={(e) => setCustomWorkspacePath(e.target.value)}
                              />
                            </div>
                          ),
                          okText: '确认更改',
                          cancelText: '取消',
                          onOk: () => handleCreateWorkspace(true),
                        })}
                      >
                        更改目录
                      </Button>
                    </div>
                  }
                  description={
                    <Typography.Text code style={{ marginTop: 8, display: 'block' }}>
                      {workspaceStatus.local_working_dir}
                    </Typography.Text>
                  }
                />
              ) : (
                <Alert
                  type="info"
                  showIcon
                  message="首次使用：配置工作目录"
                  description={
                    <div style={{ marginTop: 12 }}>
                      <Typography.Paragraph type="secondary">
                        AI Agent 需要一个本地目录来存储对话记录、记忆和技能。
                        默认使用 <code>~/.fitagent</code> 目录。
                      </Typography.Paragraph>
                      <Space direction="vertical" style={{ width: '100%', marginTop: 12 }}>
                        <Button
                          type="primary"
                          loading={workspaceSaving}
                          onClick={() => handleCreateWorkspace(false)}
                          icon={<FolderOpen size={16} />}
                        >
                          使用默认目录
                        </Button>
                        <div>
                          <Typography.Text type="secondary" style={{ marginRight: 8 }}>
                            或自定义目录：
                          </Typography.Text>
                          <Input
                            placeholder="输入自定义目录路径"
                            style={{ width: 300, marginRight: 8 }}
                            value={customWorkspacePath}
                            onChange={(e) => setCustomWorkspacePath(e.target.value)}
                          />
                          <Button
                            loading={workspaceSaving}
                            onClick={() => handleCreateWorkspace(true)}
                            disabled={!customWorkspacePath}
                          >
                            使用此目录
                          </Button>
                        </div>
                      </Space>
                    </div>
                  }
                />
              )}
            </Spin>
          </Card>

          {/* 模型配置卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={16} style={{ color: '#0EA5E9' }} />
                <span>模型配置</span>
              </div>
            }
            extra={
              <Button
                type="primary"
                size="small"
                loading={savingModel}
                onClick={handleSaveModel}
              >
                保存模型配置
              </Button>
            }
            style={{ border: 'none' }}
          >
            <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
              配置 DashScope API Key 和模型参数，控制 Agent 的响应能力和思考模式。
            </Typography.Paragraph>

            {/* API Key 状态提示 */}
            {apiKeyMasked && (
              <Alert
                type="success"
                showIcon
                style={{ marginBottom: 16, borderRadius: 10 }}
                message={
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>
                      当前 API Key：{apiKeyMasked}
                      <Tag color="#10B981" style={{ marginLeft: 8 }}>
                        已配置
                      </Tag>
                    </span>
                  </div>
                }
              />
            )}
            {!apiKeyMasked && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16, borderRadius: 10 }}
                message="首次使用配置"
                description={
                  <span>
                    请在下方填入您的 DashScope API Key 后点击「保存模型配置」即可开始使用 AI 助手。
                    获取 API Key 请访问{' '}
                    <a href="https://bailian.console.aliyun.com/" target="_blank" rel="noopener noreferrer">
                      阿里云百炼控制台
                    </a>
                  </span>
                }
              />
            )}

            <Row gutter={16}>
              <Col span={24}>
                <Form.Item
                  name="api_key"
                  label={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Key size={14} style={{ color: '#0EA5E9' }} />
                      <span>DashScope API Key</span>
                    </div>
                  }
                  help={
                    hasApiKeyInput
                      ? '输入新的 API Key 以替换当前配置；留空则清除已配置的 Key'
                      : '填入您的 DashScope API Key，从阿里云百炼控制台获取'
                  }
                >
                  <Input.Password
                    placeholder={
                      apiKeyMasked
                        ? '输入新的 API Key 或留空清除配置'
                        : '输入您的 DashScope API Key'
                    }
                    style={{ borderRadius: 10 }}
                    onChange={() => setHasApiKeyInput(true)}
                  />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={24}>
                <Form.Item
                  name="model_name"
                  label={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span>模型选择</span>
                      <Button
                        type="link"
                        size="small"
                        style={{ padding: 0, height: 'auto', fontSize: 12 }}
                        onClick={() => {
                          if (useCustomModel) {
                            setUseCustomModel(false)
                            agentForm.setFieldValue('model_name', 'qwen-turbo')
                          } else {
                            setUseCustomModel(true)
                            agentForm.setFieldValue('model_name', '')
                          }
                        }}
                      >
                        {useCustomModel ? '切换预设' : '自定义模型'}
                      </Button>
                    </div>
                  }
                  help={
                    useCustomModel
                      ? '输入阿里云百炼的模型 ID，如 qwen3.5-flash、qwen3-32b 等'
                      : '选择适合的模型，越强大的模型响应越准确但速度较慢'
                  }
                >
                  {useCustomModel ? (
                    <Input
                      placeholder="输入模型 ID，如 qwen3.5-flash"
                      style={{ borderRadius: 10 }}
                      allowClear
                    />
                  ) : (
                    <Select
                      options={modelOptions}
                      style={{ borderRadius: 10 }}
                      placeholder="选择模型"
                      showSearch
                      optionFilterProp="label"
                    />
                  )}
                </Form.Item>
                <div style={{ marginTop: -8, marginBottom: 12 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    更多模型请访问{' '}
                    <a href="https://bailian.console.aliyun.com/cn-beijing/?tab=model#/model-market" target="_blank" rel="noopener noreferrer">
                      阿里云百炼模型市场
                    </a>
                    {' '}选择适合的视觉/多模态模型 ID
                  </Typography.Text>
                </div>
              </Col>
            </Row>
          </Card>

          {/* 智能体人格配置 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Bot size={16} style={{ color: '#A78BFA' }} />
                <span>智能体人格配置</span>
              </div>
            }
            style={{ border: 'none' }}
          >
            {/* 人格预设选择器 */}
            <div style={{ display: 'flex', flexDirection: isMobile ? 'column' : 'row', alignItems: isMobile ? 'flex-start' : 'center', gap: 12, marginBottom: 20 }}>
              <Typography.Text strong>
                <Sparkles size={14} style={{ marginRight: 4, color: '#A78BFA' }} />
                人格预设
              </Typography.Text>
              <Select
                value={selectedPreset}
                onChange={(key) => {
                  if (key === 'custom') {
                    setSelectedPreset('custom')
                  } else {
                    const preset = personalityPresets.find(p => p.key === key)!
                    handleApplyPersonality(preset)
                  }
                }}
                style={{ flex: 1, maxWidth: isMobile ? '100%' : 320, borderRadius: 10 }}
                options={personalityPresets.map(p => ({
                  value: p.key,
                  label: `${p.emoji} ${p.label}`,
                }))}
              />
            </div>

            {/* 当前人格描述 */}
            {selectedPreset !== 'custom' && (
              <Alert
                type="info"
                showIcon
                style={{ marginBottom: 20, borderRadius: 10 }}
                message={
                  (() => {
                    const preset = personalityPresets.find(p => p.key === selectedPreset)
                    return preset ? `${preset.emoji} ${preset.label} — ${preset.description}` : ''
                  })()
                }
              />
            )}

            {/* 系统提示词 */}
            <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
              定义 Agent 的主要功能、使用工具的方式以及回答风格。
            </Typography.Paragraph>
            <Form.Item name="agents_md" style={{ marginBottom: 16 }}>
              <Input.TextArea rows={isMobile ? 6 : 10} placeholder="例如：你是 Rogers，一个专业的健身和健康管理助手..." />
            </Form.Item>

            {/* 性格设定 */}
            <Typography.Paragraph type="secondary" style={{ marginBottom: 12 }}>
              定义 Agent 的个性、语气和沟通风格。
            </Typography.Paragraph>
            <Form.Item name="soul_md" style={{ marginBottom: 0 }}>
              <Input.TextArea rows={isMobile ? 4 : 6} placeholder="例如：温暖、专业、鼓励型，用简洁的语言回答问题..." />
            </Form.Item>
          </Card>

          {/* 上下文管理 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={16} style={{ color: '#F59E0B' }} />
                <span>上下文管理</span>
              </div>
            }
            extra={
              <Space>
                <Button
                  type="text"
                  size="small"
                  icon={<ReloadOutlined />}
                  onClick={fetchContextData}
                >
                  刷新
                </Button>
                <Button
                  type="text"
                  size="small"
                  icon={<ExperimentOutlined />}
                  onClick={handleCompact}
                  loading={compactLoading}
                >
                  压缩上下文
                </Button>
                <Popconfirm
                  title="确认清理"
                  description="确定要清理所有工具结果缓存吗？"
                  onConfirm={handleClearCache}
                >
                  <Button type="text" size="small" danger icon={<DeleteOutlined />}>
                    清理缓存
                  </Button>
                </Popconfirm>
              </Space>
            }
            style={{ border: 'none' }}
          >
            <Spin spinning={contextLoading}>
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={12} sm={6}>
                  <Card size="small">
                    <Statistic
                      title="缓存文件"
                      value={contextStats?.cache_file_count || 0}
                      valueStyle={{ fontSize: 20 }}
                    />
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card size="small">
                    <Statistic
                      title="缓存大小"
                      value={(contextStats?.cache_total_size_bytes || 0) / 1024}
                      precision={1}
                      suffix="KB"
                      valueStyle={{ fontSize: 20 }}
                    />
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card size="small">
                    <Statistic
                      title="压缩次数"
                      value={`${contextStats?.compaction_count_today || 0} / ${contextStats?.compaction_count_total || 0}`}
                      valueStyle={{ fontSize: 20 }}
                    />
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>今日 / 总计</Typography.Text>
                  </Card>
                </Col>
                <Col xs={12} sm={6}>
                  <Card size="small">
                    <Statistic
                      title="平均响应"
                      value={contextStats?.avg_response_tokens || 0}
                      suffix="tokens"
                      valueStyle={{ fontSize: 20 }}
                    />
                  </Card>
                </Col>
              </Row>

              <Table
                dataSource={cacheList}
                columns={[
                  {
                    title: '工具名称',
                    dataIndex: 'tool_name',
                    key: 'tool_name',
                  },
                  {
                    title: '大小',
                    dataIndex: 'size_bytes',
                    key: 'size_bytes',
                    render: (bytes: number) => `${(bytes / 1024).toFixed(1)} KB`,
                  },
                  {
                    title: '时间',
                    dataIndex: 'created_at',
                    key: 'created_at',
                  },
                  {
                    title: '操作',
                    key: 'action',
                    render: (_: unknown, record: CacheEntry) => (
                      <Button
                        type="text"
                        size="small"
                        icon={<EyeOutlined />}
                        onClick={() => handleViewCache(record.id)}
                      >
                        查看
                      </Button>
                    ),
                  },
                ]}
                rowKey="id"
                pagination={{ pageSize: 5 }}
                locale={{ emptyText: '暂无缓存' }}
                size="small"
              />
            </Spin>
          </Card>

          <Button type="primary" loading={saving} htmlType="submit" size="large">
            保存配置
          </Button>
        </Space>
      </Form>

      {/* 缓存内容弹窗 */}
      <Modal
        title="缓存内容"
        open={cacheModalVisible}
        onCancel={() => setCacheModalVisible(false)}
        footer={null}
        width={800}
        style={{ maxHeight: '80vh', overflow: 'auto' }}
      >
        <pre className="cache-content">
          {cacheContent}
        </pre>
      </Modal>
    </div>
  )
}

export default AgentConfig
