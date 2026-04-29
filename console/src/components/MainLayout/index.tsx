import React, { useState } from 'react'
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Button,
  Typography,
} from 'antd'
import {
  DashboardOutlined,
  HeartOutlined,
  FireOutlined,
  CoffeeOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
  RobotOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import type { MenuProps } from 'antd'
import AIAssistant from '../AIAssistant'

const { Header, Content, Sider } = Layout
const { Title } = Typography

interface NavItem {
  key: string
  icon: React.ReactNode
  label: string
}

const navItems: NavItem[] = [
  { key: '/', icon: <DashboardOutlined />, label: '概览' },
  { key: '/health', icon: <HeartOutlined />, label: '健康数据' },
  { key: '/training', icon: <FireOutlined />, label: '训练计划' },
  { key: '/diet', icon: <CoffeeOutlined />, label: '饮食管理' },
  { key: '/user', icon: <UserOutlined />, label: '个人中心' },
  { key: '/agent-config', icon: <RobotOutlined />, label: 'Agent 配置' },
]

const menuItems: MenuProps['items'] = navItems.map(item => ({ ...item }))

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [collapsed, setCollapsed] = useState(false)
  const [rightDrawerOpen, setRightDrawerOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/user'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        theme="dark"
        style={{ overflow: 'auto', height: '100vh', position: 'fixed', left: 0, top: 0, bottom: 0 }}
      >
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 16px' }}>
          <Title level={4} style={{ color: '#fff', margin: 0 }}>
            {collapsed ? 'FA' : 'FitAgent'}
          </Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 1,
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              className: 'trigger',
              style: { fontSize: 18, cursor: 'pointer' },
              onClick: () => setCollapsed(!collapsed),
            })}
            <Typography.Title level={5} style={{ margin: 0 }}>
              {navItems.find((m) => m.key === location.pathname)?.label || '概览'}
            </Typography.Title>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Button
              type="default"
              icon={<RobotOutlined />}
              onClick={() => setRightDrawerOpen(!rightDrawerOpen)}
            >
              AI助手
            </Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar style={{ backgroundColor: '#1890ff' }}>
                  {user.name?.charAt(0) || 'U'}
                </Avatar>
                <DownOutlined style={{ fontSize: 12, color: '#999' }} />
              </div>
            </Dropdown>
          </div>
        </Header>
        <Layout style={{ flexDirection: 'row', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
          <Content style={{ flex: rightDrawerOpen ? '0 0 65%' : '1 1 auto', background: '#f0f2f5', overflow: 'auto', transition: 'flex 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
            <Outlet />
          </Content>
          <div style={{
            width: rightDrawerOpen ? '35%' : 0,
            height: 'calc(100vh - 64px)',
            position: 'relative',
            background: '#fff',
            borderLeft: rightDrawerOpen ? '1px solid #f0f0f0' : 'none',
            overflow: 'hidden',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-left 0.3s ease',
          }}>
            {rightDrawerOpen && <AIAssistant />}
          </div>
        </Layout>
      </Layout>
    </Layout>
  )
}

export default MainLayout
