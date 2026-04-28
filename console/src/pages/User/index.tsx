import React, { useEffect, useState } from 'react'
import { Card, Typography, Row, Col, Avatar, Form, Input, InputNumber, Switch, TimePicker, Button, Divider, message, Descriptions } from 'antd'
import { LogoutOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { userApi, type UserProfile } from '../../services/user'

const User: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [profileForm] = Form.useForm()
  const [settingsForm] = Form.useForm()

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

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return (
    <div style={{ padding: 24 }}>
      <Typography.Title level={4} style={{ marginBottom: 24 }}>👤 个人中心</Typography.Title>

      <Row gutter={[24, 24]}>
        <Col xs={24} md={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              {loading ? (
                <Avatar size={64} icon={<LogoutOutlined />} />
              ) : (
                <Avatar size={64} style={{ backgroundColor: '#1890ff', marginBottom: 16 }}>
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
          <Card title="编辑个人信息">
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

          <Card title="⚙️ 健身目标设置" style={{ marginTop: 24 }}>
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
        </Col>
      </Row>
    </div>
  )
}

export default User
