import React, { useEffect, useState } from 'react'
import { Card, Typography, Form, Input, Button, message, Space, Tag } from 'antd'
import { RobotOutlined, SaveOutlined } from '@ant-design/icons'
import { agentApi } from '../../services/user'

const AgentConfig: React.FC = () => {
  const [agentForm] = Form.useForm()
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const data = await agentApi.getConfig()
      agentForm.setFieldsValue({ agents_md: data.agents_md, soul_md: data.soul_md })
    } catch {
      message.error('获取配置失败')
    }
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      const values = await agentForm.validateFields()
      await agentApi.updateConfig(values)
      message.success('Agent 配置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>
        <RobotOutlined /> AI Agent 配置
      </Typography.Title>

      <Form form={agentForm} layout="vertical" onFinish={handleSave}>
        <Space direction="vertical" size={24} style={{ width: '100%' }}>
          <Card title="系统提示词" extra={<Tag color="blue">agents.md</Tag>}>
            <Typography.Paragraph type="secondary">
              定义 Agent 的主要功能、使用工具的方式以及回答风格。保存后下次对话将自动使用新的提示词。
            </Typography.Paragraph>
            <Form.Item name="agents_md">
              <Input.TextArea rows={10} placeholder="例如：你是 Rogers，一个专业的健身和健康管理助手..." />
            </Form.Item>
          </Card>

          <Card title="性格设定" extra={<Tag color="green">soul.md</Tag>}>
            <Typography.Paragraph type="secondary">
              定义 Agent 的个性、语气和沟通风格。
            </Typography.Paragraph>
            <Form.Item name="soul_md">
              <Input.TextArea rows={6} placeholder="例如：温暖、专业、鼓励型，用简洁的语言回答问题..." />
            </Form.Item>
          </Card>

          <Button type="primary" icon={<SaveOutlined />} loading={saving} htmlType="submit" size="large">
            保存配置
          </Button>
        </Space>
      </Form>
    </div>
  )
}

export default AgentConfig
