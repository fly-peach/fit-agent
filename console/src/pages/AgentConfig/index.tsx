import React, { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Typography, message, Modal } from 'antd'
import { KeyOutlined, DeleteOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { agentApi } from '../../services/agent'

const { Title, Text } = Typography

const AgentConfig: React.FC = () => {
  const [hasApiKey, setHasApiKey] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form] = Form.useForm()

  const loadStatus = async () => {
    setLoading(true)
    try {
      const status = await agentApi.getApiKeyStatus()
      setHasApiKey(status.has_api_key)
    } catch {
      // 静默失败
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  const handleSave = async (values: { api_key: string }) => {
    setSaving(true)
    try {
      await agentApi.setApiKey(values.api_key)
      message.success('API Key 设置成功，有效期为 7 天')
      setHasApiKey(true)
      form.resetFields()
    } catch (e: any) {
      message.error(e.message || '设置失败')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = () => {
    Modal.confirm({
      title: '确认删除',
      content: '删除后 Agent 将无法调用模型服务，确定要删除 API Key 吗？',
      okText: '确认删除',
      cancelText: '取消',
      okButtonProps: { danger: true },
      onOk: async () => {
        try {
          await agentApi.deleteApiKey()
          message.success('API Key 已删除')
          setHasApiKey(false)
        } catch (e: any) {
          message.error(e.message || '删除失败')
        }
      },
    })
  }

  return (
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '24px 16px' }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        <KeyOutlined style={{ marginRight: 8 }} />
        Agent 配置
      </Title>

      {/* ── API Key 状态 ── */}
      <Card
        title="API Key 状态"
        style={{ marginBottom: 24, borderRadius: 16 }}
      >
        {loading ? (
          <Text type="secondary">加载中...</Text>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {hasApiKey ? (
              <>
                <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
                <Text>已配置 API Key（7 天内有效）</Text>
                <Button
                  danger
                  icon={<DeleteOutlined />}
                  onClick={handleDelete}
                  style={{ marginLeft: 'auto' }}
                >
                  删除
                </Button>
              </>
            ) : (
              <>
                <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
                <Text type="secondary">未配置 API Key，Agent 无法调用模型服务</Text>
              </>
            )}
          </div>
        )}
      </Card>

      {/* ── 设置 API Key ── */}
      <Card
        title="设置 API Key"
        style={{ borderRadius: 16 }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          autoComplete="off"
        >
          <Form.Item
            name="api_key"
            label="API Key"
            rules={[
              { required: true, message: '请输入 API Key' },
              { min: 8, message: 'API Key 长度不能少于 8 位' },
            ]}
          >
            <Input.Password
              placeholder="输入你的 API Key"
              prefix={<KeyOutlined />}
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={saving}
              block
              size="large"
              style={{ borderRadius: 20 }}
            >
              保存
            </Button>
          </Form.Item>
        </Form>

        <Text type="secondary" style={{ fontSize: 12 }}>
          API Key 会被缓存 7 天。每次调用 Agent 时会自动刷新有效期。
          删除后需要重新设置才能继续使用 Agent 服务。
        </Text>
      </Card>
    </div>
  )
}

export default AgentConfig
