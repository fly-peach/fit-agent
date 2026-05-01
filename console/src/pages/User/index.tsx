import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Avatar, Form, Input, InputNumber, Switch, TimePicker, Button, Divider, message, Descriptions } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import { User } from 'lucide-react'
import dayjs from 'dayjs'
import { userApi, type UserProfile, agentApi } from '../../services/user'

const UserPage: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [profileForm] = Form.useForm()
  const [settingsForm] = Form.useForm()
  const [agentForm] = Form.useForm()
  const [agentConfigLoading, setAgentConfigLoading] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const profileData = await userApi.getProfile()
      setProfile(profileData)
      profileForm.setFieldsValue({ name: profileData.name, avatar: profileData.avatar || '' })

      const settingsData = await userApi.getSettings()
      settingsForm.setFieldsValue({
        calorieGoal: settingsData.calorieGoal,
        proteinGoal: settingsData.proteinGoal,
        carbsGoal: settingsData.carbsGoal,
        fatGoal: settingsData.fatGoal,
        waterGoal: settingsData.waterGoal,
        weightGoal: settingsData.weightGoal,
        weeklyTrainingGoal: settingsData.weeklyTrainingGoal,
        notificationEnabled: settingsData.notificationEnabled,
        reminderTime: dayjs(settingsData.reminderTime, 'HH:mm:ss'),
      })

      const agentData = await agentApi.getConfig()
      agentForm.setFieldsValue({ agents_md: agentData.agents_md, soul_md: agentData.soul_md })
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async () => {
    try {
      const values = await profileForm.validateFields()
      await userApi.updateProfile(values)
      message.success('更新成功')
      fetchData()
    } catch {
      message.error('更新失败')
    }
  }

  const handleUpdateSettings = async () => {
    try {
      const values = await settingsForm.validateFields()
      await userApi.updateSettings({
        ...values,
        reminderTime: values.reminderTime?.format('HH:mm') || '07:00',
      })
      message.success('设置已保存')
      fetchData()
    } catch {
      message.error('保存失败')
    }
  }

  const handleSaveAgentConfig = async () => {
    try {
      setAgentConfigLoading(true)
      const values = await agentForm.validateFields()
      await agentApi.updateConfig(values)
      message.success('Agent 配置已保存')
    } catch {
      message.error('保存失败')
    } finally {
      setAgentConfigLoading(false)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return (
    <div className="fitagent-page-enter" style={{ padding: 24 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <span className="fitagent-icon-badge" style={{ background: '#F5F3FF', color: '#8B5CF6' }}>
          <User size={18} />
        </span>
        <Typography.Title level={4} style={{ margin: 0 }}>个人中心</Typography.Title>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card style={{ border: 'none', background: 'linear-gradient(135deg, #E0F2FE 0%, #F5F3FF 100%)' }}>
            <div style={{ textAlign: 'center' }}>
              {loading ? (
                <Avatar size={64} icon={<LogoutOutlined />} />
              ) : (
                <Avatar size={64} style={{ backgroundColor: '#0EA5E9', marginBottom: 16, fontWeight: 700 }}>
                  {profile?.avatar || profile?.name?.charAt(0) || 'U'}
                </Avatar>
              )}
              <Typography.Title level={4} style={{ margin: '0 0 4px' }}>{loading ? '-' : profile?.name}</Typography.Title>
              <Typography.Text type="secondary">{loading ? '-' : profile?.email}</Typography.Text>
            </div>
            <Divider />
            {profile && !loading && (
              <Descriptions column={1} size="small">
                <Descriptions.Item label="用户ID">{profile.userId}</Descriptions.Item>
                <Descriptions.Item label="角色">{profile.role}</Descriptions.Item>
                <Descriptions.Item label="注册时间">{dayjs(profile.createdAt).format('YYYY-MM-DD')}</Descriptions.Item>
              </Descriptions>
            )}
            <Divider />
            <Button danger icon={<LogoutOutlined />} block onClick={handleLogout}>退出登录</Button>
          </Card>
        </Col>

        <Col xs={24} md={16}>
          <Card title="编辑个人信息" style={{ border: 'none' }}>
            <Form form={profileForm} layout="vertical" onFinish={handleUpdateProfile}>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="name" label="姓名" rules={[{ required: true }]}>
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="avatar" label="头像字母">
                    <Input maxLength={2} />
                  </Form.Item>
                </Col>
              </Row>
              <Button type="primary" htmlType="submit">保存</Button>
            </Form>
          </Card>

          <Card title="健身目标设置" style={{ marginTop: 24, border: 'none' }}>
            <Form form={settingsForm} layout="vertical" onFinish={handleUpdateSettings}>
              <Typography.Text type="secondary">饮食目标</Typography.Text>
              <Row gutter={16} style={{ marginTop: 8 }}>
                <Col span={8}><Form.Item name="calorieGoal" label="每日热量"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
                <Col span={8}><Form.Item name="proteinGoal" label="蛋白质"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
                <Col span={8}><Form.Item name="carbsGoal" label="碳水"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}><Form.Item name="fatGoal" label="脂肪"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
                <Col span={8}><Form.Item name="waterGoal" label="饮水"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
                <Col span={8}><Form.Item name="weightGoal" label="目标体重"><InputNumber style={{ width: '100%' }} /></Form.Item></Col>
              </Row>

              <Typography.Text type="secondary" style={{ marginTop: 8, display: 'block' }}>训练目标</Typography.Text>
              <Form.Item name="weeklyTrainingGoal" label="每周训练目标">
                <InputNumber style={{ width: '100%' }} />
              </Form.Item>

              <Typography.Text type="secondary" style={{ marginTop: 8, display: 'block' }}>提醒设置</Typography.Text>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="notificationEnabled" label="开启通知" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="reminderTime" label="提醒时间">
                    <TimePicker style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              <Button type="primary" htmlType="submit">保存设置</Button>
            </Form>
          </Card>

          <Card title="AI Agent 配置" style={{ marginTop: 24, border: 'none' }}>
            <Form form={agentForm} layout="vertical" onFinish={handleSaveAgentConfig}>
              <Form.Item
                name="agents_md"
                label="系统提示词 (agents.md)"
                help="定义 Agent 的主要功能、使用工具的方式以及回答风格"
              >
                <Input.TextArea
                  rows={8}
                  placeholder="例如：你是 Rogers，一个专业的健身和健康管理助手..."
                />
              </Form.Item>
              <Form.Item
                name="soul_md"
                label="性格设定 (soul.md)"
                help="定义 Agent 的个性、语气和沟通风格"
              >
                <Input.TextArea
                  rows={6}
                  placeholder="例如：温暖、专业、鼓励型，用简洁的语言回答问题..."
                />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={agentConfigLoading}>保存配置</Button>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default UserPage