import React, { useEffect, useState } from 'react'
import { Card, Typography, Form, Input, Button, message, Space, Tag, Select, Switch, Row, Col, Alert, Tooltip } from 'antd'
import { Bot, Key, Cpu, Brain, RotateCcw, Info } from 'lucide-react'
import { agentApi, type DefaultConfig } from '../../services/user'

const modelOptions = [
  { value: 'qwen-turbo', label: 'Qwen Turbo (快速)' },
  { value: 'qwen-plus', label: 'Qwen Plus (均衡)' },
  { value: 'qwen-max', label: 'Qwen Max (强大)' },
  { value: 'qwen-max-longcontext', label: 'Qwen Max LongContext (长文本)' },
  { value: 'qwen2.5-72b-instruct', label: 'Qwen2.5 72B (最强)' },
  { value: 'qwen2.5-32b-instruct', label: 'Qwen2.5 32B' },
  { value: 'qwen2.5-14b-instruct', label: 'Qwen2.5 14B' },
  { value: 'qwen2.5-7b-instruct', label: 'Qwen2.5 7B (轻量)' },
  { value: 'qwen3.5-plus', label: 'Qwen3.5-Plus (多模态推荐)' },
  { value: 'qwen-vl-max', label: 'Qwen2.5-VL Max (视觉理解最强)' },
  { value: 'qwen-vl-plus', label: 'Qwen2.5-VL Plus (视觉理解均衡)' },
  { value: 'qwen2.5-vl-72b', label: 'Qwen2.5-VL 72B (开源视觉理解)' },
  { value: 'qwen2.5-vl-32b', label: 'Qwen2.5-VL 32B (视觉性价比)' },
  { value: 'qwen2.5-vl-7b', label: 'Qwen2.5-VL 7B (视觉轻量)' },
  { value: 'qwen3-vl-plus', label: 'Qwen3-VL Plus (新一代视觉)' },
  { value: 'qwen3-vl-flash', label: 'Qwen3-VL Flash (新一代视觉快速)' },
]

const AgentConfig: React.FC = () => {
  const [agentForm] = Form.useForm()
  const [saving, setSaving] = useState(false)
  const [isCustomApiKey, setIsCustomApiKey] = useState(false)
  const [defaultConfig, setDefaultConfig] = useState<DefaultConfig | null>(null)
  const [apiKeyMasked, setApiKeyMasked] = useState('')

  useEffect(() => {
    fetchConfig()
    fetchDefaults()
  }, [])

  const fetchConfig = async () => {
    try {
      const data = await agentApi.getConfig()
      agentForm.setFieldsValue({
        agents_md: data.agents_md,
        soul_md: data.soul_md,
        api_key: data.api_key,
        model_name: data.model_name,
        enable_thinking: data.enable_thinking,
        multimodality: data.multimodality,
      })
      setIsCustomApiKey(data.is_custom_api_key)
      setApiKeyMasked(data.api_key_masked)
    } catch {
      message.error('获取配置失败')
    }
  }

  const fetchDefaults = async () => {
    try {
      const data = await agentApi.getDefaults()
      setDefaultConfig(data)
    } catch {
      // ignore
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

  const handleResetToDefault = async () => {
    if (!defaultConfig) {
      message.warning('无法获取默认配置')
      return
    }
    try {
      setSaving(true)
      await agentApi.updateConfig({
        agents_md: defaultConfig.agents_md,
        soul_md: defaultConfig.soul_md,
        model_name: defaultConfig.model_name,
        enable_thinking: defaultConfig.enable_thinking,
        multimodality: false,
      })
      message.success('已恢复默认提示词配置')
      fetchConfig()
    } catch {
      message.error('恢复失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#F5F3FF', color: '#A78BFA' }}>
          <Bot size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>AI Agent 配置</Typography.Title>
      </div>

      <Form form={agentForm} layout="vertical" onFinish={handleSave}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          {/* 模型配置卡片 */}
          <Card
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Cpu size={16} style={{ color: '#0EA5E9' }} />
                <span>模型配置</span>
              </div>
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
              <Col span={16}>
                <Form.Item
                  name="model_name"
                  label="模型选择"
                  help="选择适合的模型，越强大的模型响应越准确但速度较慢"
                >
                  <Select
                    options={modelOptions}
                    style={{ borderRadius: 10 }}
                    placeholder="选择模型"
                    showSearch
                    optionFilterProp="label"
                  />
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
              <Col span={8}>
                <Form.Item
                  name="enable_thinking"
                  label={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <Brain size={14} style={{ color: '#10B981' }} />
                      <span>启用思考模式</span>
                    </div>
                  }
                  help="开启后模型会先思考再回答，结果更准确"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  name="multimodality"
                  label="多模态支持"
                  help="开启后可识别图片内容，支持图片上传对话"
                  valuePropName="checked"
                >
                  <Switch />
                </Form.Item>
              </Col>
            </Row>
          </Card>

          {/* 系统提示词卡片 */}
          <Card
            title="系统提示词"
            extra={
              <Button
                type="link"
                icon={<RotateCcw size={14} />}
                onClick={handleResetToDefault}
                loading={saving}
                style={{ color: '#0EA5E9' }}
              >
                恢复默认
              </Button>
            }
            style={{ border: 'none' }}
          >
            <Typography.Paragraph type="secondary">
              定义 Agent 的主要功能、使用工具的方式以及回答风格。保存后下次对话将自动使用新的提示词。
            </Typography.Paragraph>
            <Form.Item name="agents_md">
              <Input.TextArea rows={10} placeholder="例如：你是 Rogers，一个专业的健身和健康管理助手..." />
            </Form.Item>
          </Card>

          {/* 性格设定卡片 */}
          <Card
            title="性格设定"
            extra={
              <Button
                type="link"
                icon={<RotateCcw size={14} />}
                onClick={handleResetToDefault}
                loading={saving}
                style={{ color: '#10B981' }}
              >
                恢复默认
              </Button>
            }
            style={{ border: 'none' }}
          >
            <Typography.Paragraph type="secondary">
              定义 Agent 的个性、语气和沟通风格。
            </Typography.Paragraph>
            <Form.Item name="soul_md">
              <Input.TextArea rows={6} placeholder="例如：温暖、专业、鼓励型，用简洁的语言回答问题..." />
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