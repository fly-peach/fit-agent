import React, { useState, useEffect } from 'react'
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Button,
  Typography,
  Drawer,
} from 'antd'
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
} from '@ant-design/icons'
import { LayoutDashboard, Heart, Dumbbell, Utensils, User, Bot, Wrench, Book } from 'lucide-react'
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

const IconWrapper: React.FC<{ children: React.ReactNode; color: string }> = ({ children, color }) => (
  <span style={{
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: 32,
    height: 32,
    borderRadius: 10,
    background: `${color}15`,
    fontSize: 16,
  }}>
    {children}
  </span>
)

const navItems: NavItem[] = [
  { key: '/', icon: <IconWrapper color="#0EA5E9"><LayoutDashboard size={16} /></IconWrapper>, label: '概览' },
  { key: '/health', icon: <IconWrapper color="#10B981"><Heart size={16} /></IconWrapper>, label: '健康数据' },
  { key: '/training', icon: <IconWrapper color="#F59E0B"><Dumbbell size={16} /></IconWrapper>, label: '训练计划' },
  { key: '/diet', icon: <IconWrapper color="#06B6D4"><Utensils size={16} /></IconWrapper>, label: '饮食管理' },
  { key: '/user', icon: <IconWrapper color="#8B5CF6"><User size={16} /></IconWrapper>, label: '个人中心' },
  { key: '/agent-config', icon: <IconWrapper color="#A78BFA"><Bot size={16} /></IconWrapper>, label: 'Agent 配置' },
  { key: '/skills', icon: <IconWrapper color="#F97316"><Wrench size={16} /></IconWrapper>, label: '技能管理' },
  { key: '/memory', icon: <IconWrapper color="#EC4899"><Book size={16} /></IconWrapper>, label: '记忆管理' },
]

const menuItems: MenuProps['items'] = navItems.map(item => ({ ...item }))

// Mobile bottom nav icons (no wrapper for compactness)
const mobileNavItems = [
  { key: '/', icon: <LayoutDashboard size={20} />, label: '概览', color: '#0EA5E9' },
  { key: '/health', icon: <Heart size={20} />, label: '健康', color: '#10B981' },
  { key: '/training', icon: <Dumbbell size={20} />, label: '训练', color: '#F59E0B' },
  { key: '/diet', icon: <Utensils size={20} />, label: '饮食', color: '#06B6D4' },
  { key: '/user', icon: <User size={20} />, label: '我的', color: '#8B5CF6' },
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

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [collapsed, setCollapsed] = useState(false)
  const [rightDrawerOpen, setRightDrawerOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const isMobile = useIsMobile()

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
      onClick: () => { navigate('/user'); setMobileMenuOpen(false) },
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ]

  const handleNav = (key: string) => {
    navigate(key)
    setMobileMenuOpen(false)
  }

  // Mobile bottom navigation
  if (isMobile) {
    return (
      <Layout style={{ minHeight: '100vh' }}>
        <Header
          style={{
            padding: '0 16px',
            background: 'rgba(255, 255, 255, 0.95)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 100,
            borderBottom: '1px solid #F0EDE8',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Title level={5} style={{
              margin: 0,
              color: '#0EA5E9',
              fontWeight: 800,
              fontFamily: "'Nunito', 'Noto Sans SC', sans-serif",
            }}>
              FitAgent
            </Title>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Button
              type="text"
              icon={<Bot size={18} />}
              onClick={() => setRightDrawerOpen(!rightDrawerOpen)}
              size="small"
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar style={{ backgroundColor: '#0EA5E9', cursor: 'pointer' }}>
                {user.name?.charAt(0) || 'U'}
              </Avatar>
            </Dropdown>
          </div>
        </Header>
        <Layout style={{ flexDirection: 'row', height: 'calc(100vh - 56px)', overflow: 'hidden' }}>
          <Content style={{ flex: 1, background: 'transparent', overflow: 'auto', transition: 'flex 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
            <Outlet />
          </Content>
          <div style={{
            width: rightDrawerOpen ? '100%' : 0,
            height: 'calc(100vh - 56px)',
            position: 'fixed',
            right: 0,
            top: 56,
            zIndex: 99,
            background: '#fff',
            overflow: 'hidden',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          }}>
            {rightDrawerOpen && <AIAssistant />}
          </div>
        </Layout>
        {/* Mobile bottom navigation */}
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          height: 56,
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(12px)',
          borderTop: '1px solid #F0EDE8',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-around',
          zIndex: 100,
          paddingLeft: 4,
          paddingRight: 4,
        }}>
          {mobileNavItems.map(item => (
            <div
              key={item.key}
              onClick={() => handleNav(item.key)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 2,
                cursor: 'pointer',
                padding: '4px 12px',
                borderRadius: 8,
                background: location.pathname === item.key ? `${item.color}12` : 'transparent',
                color: location.pathname === item.key ? item.color : '#999',
                transition: 'all 0.2s',
                flex: 1,
              }}
            >
              {item.icon}
              <span style={{ fontSize: 10, lineHeight: 1 }}>{item.label}</span>
            </div>
          ))}
        </div>
      </Layout>
    )
  }

  // Desktop layout
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        width={240}
        theme="light"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
          background: 'linear-gradient(180deg, #FFFFFF 0%, #F8F6F3 100%)',
          borderRight: '1px solid #F0EDE8',
        }}
      >
        <div style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '0 16px',
          borderBottom: '1px solid #F0EDE8',
        }}>
          <Title level={4} style={{
            color: '#0EA5E9',
            margin: 0,
            fontWeight: 800,
            fontFamily: "'Nunito', 'Noto Sans SC', sans-serif",
          }}>
            {collapsed ? 'FA' : 'FitAgent'}
          </Title>
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          style={{ borderRight: 'none' }}
        />
      </Sider>
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'margin-left 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: 'rgba(255, 255, 255, 0.85)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 1,
            borderBottom: '1px solid #F0EDE8',
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
              icon={<Bot size={16} />}
              onClick={() => setRightDrawerOpen(!rightDrawerOpen)}
            >
              AI助手
            </Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Avatar style={{ backgroundColor: '#0EA5E9' }}>
                  {user.name?.charAt(0) || 'U'}
                </Avatar>
                <DownOutlined style={{ fontSize: 12, color: '#999' }} />
              </div>
            </Dropdown>
          </div>
        </Header>
        <Layout style={{ flexDirection: 'row', height: 'calc(100vh - 64px)', overflow: 'hidden' }}>
          <Content style={{ flex: rightDrawerOpen ? '0 0 60%' : '1 1 auto', background: 'transparent', overflow: 'auto', transition: 'flex 0.3s cubic-bezier(0.4, 0, 0.2, 1)' }}>
            <Outlet />
          </Content>
          <div style={{
            width: rightDrawerOpen ? '40%' : 0,
            height: 'calc(100vh - 64px)',
            position: 'relative',
            background: '#fff',
            borderLeft: rightDrawerOpen ? '1px solid #F0EDE8' : 'none',
            overflow: 'hidden',
            transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-left 0.3s ease',
          }}>
            {rightDrawerOpen && <AIAssistant />}
          </div>
        </Layout>
      </Layout>
      {/* Mobile menu drawer for tablet */}
      <Drawer
        title="菜单"
        placement="left"
        onClose={() => setMobileMenuOpen(false)}
        open={mobileMenuOpen}
        width={240}
        styles={{ body: { padding: 0 } }}
      >
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => handleNav(key)}
        />
      </Drawer>
    </Layout>
  )
}

export default MainLayout
