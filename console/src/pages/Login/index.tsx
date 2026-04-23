import React, { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
} from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../services/auth'

const Login: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [registerName, setRegisterName] = useState('')
  const [registerEmail, setRegisterEmail] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const navigate = useNavigate()

  const handleLogin = async () => {
    if (!email || !password) {
      setSnackbar({ open: true, message: '请输入邮箱和密码', severity: 'error' })
      return
    }

    setLoading(true)
    try {
      const result = await authApi.login({ email, password })
      localStorage.setItem('token', result.token)
      localStorage.setItem('user', JSON.stringify(result.user))
      setSnackbar({ open: true, message: '登录成功', severity: 'success' })
      navigate('/')
    } catch {
      setSnackbar({ open: true, message: '邮箱或密码错误', severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async () => {
    if (!registerName || !registerEmail || !registerPassword) {
      setSnackbar({ open: true, message: '请填写所有字段', severity: 'error' })
      return
    }

    if (registerPassword.length < 6) {
      setSnackbar({ open: true, message: '密码至少6位', severity: 'error' })
      return
    }

    try {
      const result = await authApi.register({
        name: registerName,
        email: registerEmail,
        password: registerPassword,
      })
      localStorage.setItem('token', result.token)
      localStorage.setItem('user', JSON.stringify(result.user))
      setSnackbar({ open: true, message: '注册成功', severity: 'success' })
      setRegisterOpen(false)
      navigate('/')
    } catch {
      setSnackbar({ open: true, message: '注册失败，邮箱可能已被使用', severity: 'error' })
    }
  }

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card sx={{ width: 400, maxWidth: '90vw' }}>
        <CardContent sx={{ p: 3 }}>
          <Typography variant="h5" component="div" gutterBottom align="center" color="primary">
            FitAgent 健身管理平台
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="邮箱"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              fullWidth
            />
            <TextField
              label="密码"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              fullWidth
            />
            <Button
              variant="contained"
              fullWidth
              onClick={handleLogin}
              disabled={loading}
            >
              登录
            </Button>
            <Button
              variant="outlined"
              fullWidth
              onClick={() => setRegisterOpen(true)}
            >
              注册新账号
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 2 }}>
            测试账号: test@test.com / 123456
          </Typography>
        </CardContent>
      </Card>

      <Dialog open={registerOpen} onClose={() => setRegisterOpen(false)}>
        <DialogTitle>注册新账号</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
            <TextField
              label="用户名"
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
              fullWidth
            />
            <TextField
              label="邮箱"
              type="email"
              value={registerEmail}
              onChange={(e) => setRegisterEmail(e.target.value)}
              fullWidth
            />
            <TextField
              label="密码"
              type="password"
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
              fullWidth
              helperText="至少6位"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRegisterOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleRegister}>注册</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  )
}

export default Login