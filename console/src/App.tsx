import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { MainLayout } from './components'
import { Login, Dashboard, Health, Training, Diet, User } from './pages'

const App: React.FC = () => {
  const PrivateRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
    const token = localStorage.getItem('token')
    return token ? children : <Navigate to="/login" replace />
  }

  return (
    <ConfigProvider locale={zhCN}>
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
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
