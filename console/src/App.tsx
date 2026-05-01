import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { MainLayout } from './components'
import { Login, Dashboard, Health, Training, Diet, User, AgentConfig } from './pages'

const theme = {
  token: {
    colorPrimary: '#0EA5E9',
    colorSuccess: '#10B981',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    colorInfo: '#06B6D4',
    borderRadius: 12,
    borderRadiusLG: 16,
    borderRadiusXS: 6,
    borderRadiusSM: 8,
    borderRadiusOuter: 20,
    fontFamily: "'Noto Sans SC', 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif",
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
    boxShadowSecondary: '0 4px 16px rgba(0, 0, 0, 0.1)',
    boxShadowTertiary: '0 1px 2px rgba(0, 0, 0, 0.03)',
    colorText: '#2D3436',
    colorTextSecondary: '#636E72',
    colorTextTertiary: '#B2BEC3',
    colorBgLayout: 'transparent',
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    colorBorder: '#F0EDE8',
    colorBorderSecondary: '#F5F2ED',
  },
  components: {
    Card: {
      borderRadiusLG: 16,
      boxShadowTertiary: '0 2px 12px rgba(0, 0, 0, 0.06)',
    },
    Button: {
      borderRadius: 20,
      controlHeight: 40,
      paddingInline: 24,
    },
    Input: {
      borderRadius: 12,
      paddingInline: 16,
    },
    Select: {
      borderRadius: 12,
    },
    Tag: {
      borderRadius: 8,
      paddingInline: 10,
      paddingBlock: 2,
    },
    Table: {
      borderRadius: 12,
      headerBg: '#FAFAF7',
      rowHoverBg: '#FFF8F0',
    },
    Menu: {
      itemActiveBg: '#F0F9FF',
      itemHoverBg: '#F0F9FF',
      itemSelectedBg: '#E0F2FE',
      itemSelectedColor: '#0EA5E9',
    },
    Avatar: {
      borderRadius: 12,
    },
    Progress: {
      defaultColor: '#0EA5E9',
    },
    Statistic: {
      contentFontSize: 28,
    },
    Modal: {
      borderRadiusLG: 20,
    },
    Drawer: {
      borderRadiusLG: 20,
    },
  },
}

const App: React.FC = () => {
  const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
    const token = localStorage.getItem('token')
    return token ? children : <Navigate to="/login" replace />
  }

  return (
    <ConfigProvider locale={zhCN} theme={theme as any}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainLayout />
              </PrivateRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="health" element={<Health />} />
            <Route path="training" element={<Training />} />
            <Route path="diet" element={<Diet />} />
            <Route path="user" element={<User />} />
            <Route path="agent-config" element={<AgentConfig />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
