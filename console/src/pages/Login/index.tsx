import React, { useState } from 'react'
import { Form, Input, Button, Card, Typography, Modal, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../services/auth'

const Login: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [registerForm] = Form.useForm()
  const navigate = useNavigate()

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true)
    try {
      const result = await authApi.login(values)
      localStorage.setItem('token', result.token)
      localStorage.setItem('user', JSON.stringify(result.user))
      message.success('登录成功')
      navigate('/')
    } catch {
      message.error('邮箱或密码错误')
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    try {
      const values = await registerForm.validateFields()
      const result = await authApi.register(values)
      localStorage.setItem('token', result.token)
      localStorage.setItem('user', JSON.stringify(result.user))
      message.success('注册成功')
      setRegisterOpen(false)
      navigate('/')
    } catch {
      message.error('注册失败，邮箱可能已被使用')
    }
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card style={{ width: 400, maxWidth: '90vw' }}>
        <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 24, color: '#1890ff' }}>
          FitAgent 健身管理平台
        </Typography.Title>
        <Form onFinish={handleLogin} size="large">
          <Form.Item
            name="email"
            rules={[{ required: true, message: '请输入邮箱', type: 'email' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="邮箱" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              登录
            </Button>
          </Form.Item>
          <Form.Item>
            <Button block onClick={() => setRegisterOpen(true)}>
              注册新账号
            </Button>
          </Form.Item>
        </Form>
        <Typography.Text type="secondary" style={{ display: 'block', textAlign: 'center', fontSize: 12 }}>
          测试账号: test@test.com / 123456
        </Typography.Text>
      </Card>

      <Modal
        title="注册新账号"
        open={registerOpen}
        onCancel={() => setRegisterOpen(false)}
        onOk={handleRegister}
        okText="注册"
        cancelText="取消"
      >
        <Form form={registerForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            name="name"
            label="用户名"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ required: true, message: '请输入邮箱', type: 'email' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6位' },
            ]}
          >
            <Input.Password />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Login
