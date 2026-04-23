import React, { useEffect, useState } from 'react'
import {
  Card,
  Descriptions,
  Avatar,
  Typography,
  Form,
  Input,
  InputNumber,
  Switch,
  TimePicker,
  Button,
  message,
  Divider,
  Row,
  Col,
} from 'antd'
import {
  UserOutlined,
  SettingOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import dayjs from 'dayjs'
import { userApi, type UserProfile, UserSettings } from '../../services/user'
import styles from './User.module.css'

const { Title, Text } = Typography

const User: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [settings, setSettings] = useState<UserSettings | null>(null)
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
      profileForm.setFieldsValue({
        name: profileData.name,
        avatar: profileData.avatar,
      })

      const settingsData = await userApi.getSettings()
      setSettings(settingsData)
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

  const handleUpdateProfile = async (values: { name: string; avatar: string }) => {
    try {
      await userApi.updateProfile(values)
      message.success('更新成功')
      fetchData()
    } catch {
      message.error('更新失败')
    }
  }

  const handleUpdateSettings = async (values: Partial<UserSettings> & { reminderTime: dayjs.Dayjs }) => {
    try {
      await userApi.updateSettings({
        ...values,
        reminderTime: values.reminderTime?.format('HH:mm'),
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
    <div className={styles.container}>
      <Title level={3}>
        <UserOutlined /> 个人中心
      </Title>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card loading={loading}>
            <div className={styles.profileHeader}>
              <Avatar size={64} style={{ backgroundColor: '#1890ff' }}>
                {profile?.avatar || profile?.name?.charAt(0) || 'U'}
              </Avatar>
              <Title level={4} style={{ margin: '16px 0 0' }}>
                {profile?.name}
              </Title>
              <Text type="secondary">{profile?.email}</Text>
            </div>
            <Divider />
            <Descriptions column={1} size="small">
              <Descriptions.Item label="用户ID">{profile?.userId}</Descriptions.Item>
              <Descriptions.Item label="角色">{profile?.role}</Descriptions.Item>
              <Descriptions.Item label="注册时间">
                {dayjs(profile?.createdAt).format('YYYY-MM-DD')}
              </Descriptions.Item>
            </Descriptions>
            <Divider />
            <Button danger block onClick={handleLogout}>
              退出登录
            </Button>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="编辑个人信息" loading={loading}>
            <Form form={profileForm} onFinish={handleUpdateProfile} layout="vertical">
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="name" label="姓名">
                    <Input />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="avatar" label="头像字母">
                    <Input maxLength={2} />
                  </Form.Item>
                </Col>
              </Row>
              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                  保存
                </Button>
              </Form.Item>
            </Form>
          </Card>

          <Card
            title={<><SettingOutlined /> 健身目标设置</>}
            loading={loading}
            style={{ marginTop: 16 }}
          >
            <Form form={settingsForm} onFinish={handleUpdateSettings} layout="vertical">
              <Title level={5}>饮食目标</Title>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="calorieGoal" label="每日热量目标">
                    <InputNumber min={1000} max={5000} addonAfter="kcal" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="proteinGoal" label="蛋白质目标">
                    <InputNumber min={50} max={300} addonAfter="g" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="carbsGoal" label="碳水目标">
                    <InputNumber min={100} max={500} addonAfter="g" />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item name="fatGoal" label="脂肪目标">
                    <InputNumber min={20} max={150} addonAfter="g" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="waterGoal" label="饮水目标">
                    <InputNumber min={500} max={4000} addonAfter="ml" />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item name="weightGoal" label="目标体重">
                    <InputNumber min={40} max={150} addonAfter="kg" />
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Title level={5}>训练目标</Title>
              <Form.Item name="weeklyTrainingGoal" label="每周训练目标">
                <InputNumber min={1} max={7} addonAfter="次" />
              </Form.Item>

              <Divider />

              <Title level={5}>提醒设置</Title>
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item name="notificationEnabled" label="开启通知" valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item name="reminderTime" label="提醒时间">
                    <TimePicker format="HH:mm" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                  保存设置
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default User