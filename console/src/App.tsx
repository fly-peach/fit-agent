import React, { lazy, Suspense } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, Spin } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { MainLayout } from './components'

// 使用懒加载方式导入页面组件，提高初始加载速度
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Health = lazy(() => import('./pages/Health'))
const Training = lazy(() => import('./pages/Training'))
const TrainingResults = lazy(() => import('./pages/TrainingResults'))
const Diet = lazy(() => import('./pages/Diet'))
const User = lazy(() => import('./pages/User'))
const LandingPage = lazy(() => import('./pages/LandingPage'))
const AgentConfig = lazy(() => import('./pages/AgentConfig'))

// 页面加载时的骨架屏组件
const PageSkeleton: React.FC = () => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    background: '#f5f5f5'
  }}>
    <Spin size="large" />
  </div>
)

// 定义 Ant Design 的主题配置
const theme = {
  token: {
    colorPrimary: '#0EA5E9',  // 主色调
    colorSuccess: '#10B981',  // 成功色
    colorWarning: '#F59E0B',  // 警告色
    colorError: '#EF4444',    // 错误色
    colorInfo: '#06B6D4',     // 信息色
    borderRadius: 12,         // 圆角大小
    borderRadiusLG: 16,
    borderRadiusXS: 6,
    borderRadiusSM: 8,
    borderRadiusOuter: 20,
    fontFamily: "'Noto Sans SC', 'Nunito', -apple-system, BlinkMacSystemFont, sans-serif",
    fontSize: 14,
    fontSizeLG: 16,
    fontSizeHeading4: 20,
    fontSizeHeading5: 16,
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',       // 阴影效果
    boxShadowSecondary: '0 4px 16px rgba(0, 0, 0, 0.1)',
    boxShadowTertiary: '0 1px 2px rgba(0, 0, 0, 0.03)',
    colorText: '#2D3436',     // 文字颜色
    colorTextSecondary: '#636E72',
    colorTextTertiary: '#B2BEC3',
    colorBgLayout: 'transparent',  // 背景色
    colorBgContainer: '#FFFFFF',
    colorBgElevated: '#FFFFFF',
    colorBorder: '#F0EDE8',        // 边框颜色
    colorBorderSecondary: '#F5F2ED',
  },
  components: {
    Card: {
      borderRadiusLG: 16,
      boxShadowTertiary: '0 2px 12px rgba(0, 0, 0, 0.06)',
    },
    Button: {
      borderRadius: 20,           // 按钮圆角
      controlHeight: 40,          // 按钮高度
      paddingInline: 24,          // 按钮内边距
    },
    Input: {
      borderRadius: 12,           // 输入框圆角
      paddingInline: 16,          // 输入框内边距
    },
    Select: {
      borderRadius: 12,           // 下拉选择框圆角
    },
    Tag: {
      borderRadius: 8,            // 标签圆角
      paddingInline: 10,
      paddingBlock: 2,
    },
    Table: {
      borderRadius: 12,           // 表格圆角
      headerBg: '#FAFAF7',        // 表头背景色
      rowHoverBg: '#FFF8F0',      // 表格行悬停背景色
    },
    Menu: {
      itemActiveBg: '#F0F9FF',    // 菜单项激活背景色
      itemHoverBg: '#F0F9FF',     // 菜单项悬停背景色
      itemSelectedBg: '#E0F2FE',  // 菜单项选中背景色
      itemSelectedColor: '#0EA5E9',// 菜单项选中文字颜色
    },
    Avatar: {
      borderRadius: 12,           // 头像圆角
    },
    Progress: {
      defaultColor: '#0EA5E9',    // 进度条颜色
    },
    Statistic: {
      contentFontSize: 28,        // 统计数值字体大小
    },
    Modal: {
      borderRadiusLG: 20,         // 弹窗圆角
    },
    Drawer: {
      borderRadiusLG: 20,         // 抽屉圆角
    },
  },
}

const App: React.FC = () => {
  // 私有路由组件，用于检查用户是否已登录
  const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
    const token = localStorage.getItem('token')
    // 如果存在token则渲染子组件，否则重定向到登录页
    return token ? children : <Navigate to="/login" replace />
  }

  return (
    // 使用 Ant Design 的 ConfigProvider 设置全局配置
    <ConfigProvider locale={zhCN} theme={theme as any}>
      {/* 使用 BrowserRouter 提供路由能力 */}
      <BrowserRouter>
        {/* 使用 Suspense 包裹懒加载的组件，提供加载状态 */}
        <Suspense fallback={<PageSkeleton />}>
          <Routes>
            {/* 登陆页面路由 */}
            <Route path="/webpage" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            {/* 使用私有路由保护主页及子路由 */}
            <Route
              path="/"
              element={
                <PrivateRoute>
                  <MainLayout />
                </PrivateRoute>
              }
            >
              {/* 主页默认路由 */}
              <Route index element={<Dashboard />} />
              {/* 子路由：健康、训练、训练结果、饮食、用户、代理配置 */}
              <Route path="health" element={<Health />} />
              <Route path="training" element={<Training />} />
              <Route path="training-results" element={<TrainingResults />} />
              <Route path="diet" element={<Diet />} />
              <Route path="user" element={<User />} />
              <Route path="agent-config" element={<AgentConfig />} />
            </Route>
            {/* 未匹配路由重定向到主页 */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App