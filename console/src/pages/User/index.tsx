import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Avatar,
  Grid,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Snackbar,
  Alert,
  Skeleton,
  Divider,
} from '@mui/material'
import { TimePicker } from '@mui/x-date-pickers/TimePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs from 'dayjs'
import { userApi, type UserProfile } from '../../services/user'

const User: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success'
  })

  const [name, setName] = useState('')
  const [avatar, setAvatar] = useState('')

  const [calorieGoal, setCalorieGoal] = useState('2000')
  const [proteinGoal, setProteinGoal] = useState('150')
  const [carbsGoal, setCarbsGoal] = useState('250')
  const [fatGoal, setFatGoal] = useState('65')
  const [waterGoal, setWaterGoal] = useState('2000')
  const [weightGoal, setWeightGoal] = useState('')
  const [weeklyTrainingGoal, setWeeklyTrainingGoal] = useState('5')
  const [notificationEnabled, setNotificationEnabled] = useState(true)
  const [reminderTime, setReminderTime] = useState<dayjs.Dayjs | null>(dayjs())

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const profileData = await userApi.getProfile()
      setProfile(profileData)
      setName(profileData.name)
      setAvatar(profileData.avatar || '')

      const settingsData = await userApi.getSettings()
      setCalorieGoal(String(settingsData.calorieGoal))
      setProteinGoal(String(settingsData.proteinGoal))
      setCarbsGoal(String(settingsData.carbsGoal))
      setFatGoal(String(settingsData.fatGoal))
      setWaterGoal(String(settingsData.waterGoal))
      setWeightGoal(settingsData.weightGoal ? String(settingsData.weightGoal) : '')
      setWeeklyTrainingGoal(String(settingsData.weeklyTrainingGoal))
      setNotificationEnabled(settingsData.notificationEnabled)
      setReminderTime(dayjs(settingsData.reminderTime, 'HH:mm:ss'))
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateProfile = async () => {
    try {
      await userApi.updateProfile({ name, avatar })
      setSnackbar({ open: true, message: '更新成功', severity: 'success' })
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '更新失败', severity: 'error' })
    }
  }

  const handleUpdateSettings = async () => {
    try {
      await userApi.updateSettings({
        calorieGoal: parseInt(calorieGoal),
        proteinGoal: parseInt(proteinGoal),
        carbsGoal: parseInt(carbsGoal),
        fatGoal: parseInt(fatGoal),
        waterGoal: parseInt(waterGoal),
        weightGoal: weightGoal ? parseFloat(weightGoal) : undefined,
        weeklyTrainingGoal: parseInt(weeklyTrainingGoal),
        notificationEnabled,
        reminderTime: reminderTime?.format('HH:mm') || '07:00',
      })
      setSnackbar({ open: true, message: '设置已保存', severity: 'success' })
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '保存失败', severity: 'error' })
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h4" gutterBottom>👤 个人中心</Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                {loading ? <Skeleton variant="circular" width={64} height={64} /> : <>
                  <Avatar sx={{ width: 64, height: 64, bgcolor: 'primary.main', mb: 2 }}>
                    {avatar || profile?.name?.charAt(0) || 'U'}
                  </Avatar>
                  <Typography variant="h6">{profile?.name}</Typography>
                  <Typography color="text.secondary">{profile?.email}</Typography>
                </>}
                <Divider sx={{ my: 2 }} />
                <Box sx={{ textAlign: 'left' }}>
                  <Typography color="text.secondary">用户ID: {profile?.userId}</Typography>
                  <Typography color="text.secondary">角色: {profile?.role}</Typography>
                  <Typography color="text.secondary">注册时间: {dayjs(profile?.createdAt).format('YYYY-MM-DD')}</Typography>
                </Box>
                <Divider sx={{ my: 2 }} />
                <Button variant="contained" color="error" fullWidth onClick={handleLogout}>退出登录</Button>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={8}>
            <Card><CardContent>
              <Typography variant="h6" gutterBottom>编辑个人信息</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <TextField label="姓名" fullWidth value={name} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setName(e.target.value)} />
                </Grid>
                <Grid item xs={6}>
                  <TextField label="头像字母" fullWidth inputProps={{ maxLength: 2 }} value={avatar} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAvatar(e.target.value)} />
                </Grid>
              </Grid>
              <Button variant="contained" sx={{ mt: 2 }} onClick={handleUpdateProfile}>保存</Button>
            </CardContent></Card>

            <Card sx={{ mt: 3 }}><CardContent>
              <Typography variant="h6" gutterBottom>⚙️ 健身目标设置</Typography>

              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 2 }}>饮食目标</Typography>
              <Grid container spacing={2}>
                <Grid item xs={4}>
                  <TextField label="每日热量" type="number" fullWidth value={calorieGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCalorieGoal(e.target.value)} />
                </Grid>
                <Grid item xs={4}>
                  <TextField label="蛋白质" type="number" fullWidth value={proteinGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setProteinGoal(e.target.value)} />
                </Grid>
                <Grid item xs={4}>
                  <TextField label="碳水" type="number" fullWidth value={carbsGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCarbsGoal(e.target.value)} />
                </Grid>
              </Grid>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={4}>
                  <TextField label="脂肪" type="number" fullWidth value={fatGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFatGoal(e.target.value)} />
                </Grid>
                <Grid item xs={4}>
                  <TextField label="饮水" type="number" fullWidth value={waterGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWaterGoal(e.target.value)} />
                </Grid>
                <Grid item xs={4}>
                  <TextField label="目标体重" type="number" fullWidth value={weightGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWeightGoal(e.target.value)} />
                </Grid>
              </Grid>

              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 3 }}>训练目标</Typography>
              <TextField label="每周训练目标" type="number" fullWidth value={weeklyTrainingGoal} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWeeklyTrainingGoal(e.target.value)} />

              <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 3 }}>提醒设置</Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControlLabel control={<Switch checked={notificationEnabled} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setNotificationEnabled(e.target.checked)} />} label="开启通知" />
                </Grid>
                <Grid item xs={6}>
                  <TimePicker label="提醒时间" value={reminderTime} onChange={(val: dayjs.Dayjs | null) => setReminderTime(val)} />
                </Grid>
              </Grid>

              <Button variant="contained" sx={{ mt: 3 }} onClick={handleUpdateSettings}>保存设置</Button>
            </CardContent></Card>
          </Grid>
        </Grid>

        <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
        </Snackbar>
      </Box>
    </LocalizationProvider>
  )
}

export default User