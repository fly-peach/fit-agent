import React, { useEffect, useState } from 'react'
import { Card, Typography, Form, Input, Button, message, Space, Tag, Select, Row, Col, Alert, Tooltip, Modal } from 'antd'
import { Bot, Key, Cpu, Info, Sparkles } from 'lucide-react'
import { agentApi } from '../../services/user'

const modelOptions = [
  { value: 'qwen3.5-flash', label: 'Qwen3.5-Flash (多模态推荐，支持思考)', recommended: true },
  { value: 'qwen3.5-plus', label: 'Qwen3.5-Plus (更强推理)' },
  { value: 'qwen-turbo', label: 'Qwen Turbo (快速)' },
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
  const [isCustomApiKey, setIsCustomApiKey] = useState(false)
  const [apiKeyMasked, setApiKeyMasked] = useState('')
  const [useCustomModel, setUseCustomModel] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<string>('')

  const [savingModel, setSavingModel] = useState(false)
  const isMobile = useIsMobile()

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const data = await agentApi.getConfig()
      agentForm.setFieldsValue({
        agents_md: data.agents_md,
        soul_md: data.soul_md,
        api_key: data.api_key,
        model_name: data.model_name,
      })
      // 如果当前模型不在预设列表中，切换到自定义模式
      const isPreset = modelOptions.some(opt => opt.value === data.model_name)
      setUseCustomModel(!isPreset)
      // 检测当前人格配置匹配的预设
      const matchedPreset = personalityPresets.find(
        p => p.key !== 'custom' && p.agents_md === data.agents_md && p.soul_md === data.soul_md,
      )
      setSelectedPreset(matchedPreset ? matchedPreset.key : 'custom')
      setIsCustomApiKey(data.is_custom_api_key)
      setApiKeyMasked(data.api_key_masked)
    } catch {
      message.error('获取配置失败')
    }
  }
  const handleSaveModel = async () => {
    try {
      setSavingModel(true)
      const values = agentForm.getFieldsValue(['api_key', 'model_name'])
      await agentApi.updateConfig(values)
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
      await agentApi.updateConfig(values)
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

            {/* API Key 来源提示 */}
            {apiKeyMasked && (
              <Alert
                type={isCustomApiKey ? 'success' : 'info'}
                showIcon
                style={{ marginBottom: 16, borderRadius: 10 }}
                message={
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span>
                      当前 API Key：{apiKeyMasked}
                      <Tag color={isCustomApiKey ? '#10B981' : '#0EA5E9'} style={{ marginLeft: 8 }}>
                        {isCustomApiKey ? '个人配置' : '系统环境变量'}
                      </Tag>
                    </span>
                    <Tooltip title={isCustomApiKey ? '您已配置个人专属 API Key，响应更稳定可靠' : '使用系统环境变量中的默认 API Key，如需更稳定服务请配置个人 Key'}>
                      <Info size={16} style={{ color: '#6B7280', cursor: 'help' }} />
                    </Tooltip>
                  </div>
                }
              />
            )}
            {!apiKeyMasked && (
              <Alert
                type="warning"
                showIcon
                style={{ marginBottom: 16, borderRadius: 10 }}
                message="未配置 API Key，请在下方填入您的 DashScope API Key，或联系管理员配置系统环境变量"
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
                  help="填入个人 DashScope API Key 可获得更稳定服务；留空则使用系统环境变量中的默认 Key"
                >
                  <Input.Password
                    placeholder="留空使用系统默认 API Key"
                    style={{ borderRadius: 10 }}
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
                            agentForm.setFieldValue('model_name', 'qwen3.5-flash')
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

          <Button type="primary" loading={saving} htmlType="submit" size="large">
            保存配置
          </Button>
        </Space>
      </Form>
    </div>
  )
}

export default AgentConfig