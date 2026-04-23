import React, { useState } from 'react'
import { Layout, Menu, Avatar, Dropdown, Typography } from 'antd'
import {
  DashboardOutlined,
  HeartOutlined,
  FireOutlined,
  CoffeeOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import styles from './MainLayout.module.css'

const { Header, Sider, Content } = Layout
const { Text } = Typography

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '概览',
    },
    {
      key: '/health',
      icon: <HeartOutlined />,
      label: '健康数据',
    },
    {
      key: '/training',
      icon: <FireOutlined />,
      label: '训练计划',
    },
    {
      key: '/diet',
      icon: <CoffeeOutlined />,
      label: '饮食管理',
    },
    {
      key: '/user',
      icon: <UserOutlined />,
      label: '个人中心',
    },
  ]

  const userMenuItems = [
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '个人中心',
      onClick: () => navigate('/user'),
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        navigate('/login')
      },
    },
  ]

  return (
    <Layout className={styles.layout}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className={styles.sider}
      >
        <div className={styles.logo}>
          <Text strong style={{ color: '#fff', fontSize: collapsed ? 14 : 18 }}>
            {collapsed ? 'FA' : 'FitAgent'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className={styles.header}>
          <div className={styles.trigger}>
            {React.createElement(collapsed ? MenuUnfoldOutlined : MenuFoldOutlined, {
              onClick: () => setCollapsed(!collapsed),
            })}
          </div>
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <div className={styles.userInfo}>
              <Avatar style={{ backgroundColor: '#1890ff' }}>
                {user.avatar || user.name?.charAt(0) || 'U'}
              </Avatar>
              <Text style={{ marginLeft: 8 }}>{user.name}</Text>
            </div>
          </Dropdown>
        </Header>
        <Content className={styles.content}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout