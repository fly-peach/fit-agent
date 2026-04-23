import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  Alert,
  Skeleton,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs from 'dayjs'
import { trainingApi, type WeeklyStats, TrainingSchedule, RecommendedTraining } from '../../services/training'

const planTypes = [
  { value: 'strength', label: '力量训练' },
  { value: 'cardio', label: '有氧运动' },
  { value: 'flexibility', label: '柔韧训练' },
]

const intensities = [
  { value: 'low', label: '低强度' },
  { value: 'medium', label: '中等强度' },
  { value: 'high', label: '高强度' },
]

const weekDays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

const Training: React.FC = () => {
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedTraining[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [completeOpen, setCompleteOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success'
  })

  const [planName, setPlanName] = useState('')
  const [planType, setPlanType] = useState('strength')
  const [targetIntensity, setTargetIntensity] = useState('medium')
  const [estimatedDuration, setEstimatedDuration] = useState('60')
  const [scheduledDate, setScheduledDate] = useState<dayjs.Dayjs | null>(dayjs())

  const [actualDuration, setActualDuration] = useState('60')
  const [actualIntensity, setActualIntensity] = useState('medium')
  const [caloriesBurned, setCaloriesBurned] = useState('0')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [stats, sched, recs] = await Promise.all([
        trainingApi.getWeeklyStats(),
        trainingApi.getWeeklySchedule(),
        trainingApi.getRecommendations(),
      ])
      setWeeklyStats(stats)
      setSchedule(sched)
      setRecommendations(recs)
    } finally {
      setLoading(false)
    }
  }

  const handleCreatePlan = async () => {
    if (!planName || !scheduledDate) {
      setSnackbar({ open: true, message: '请填写所有字段', severity: 'error' })
      return
    }

    try {
      await trainingApi.createPlan({
        planName,
        planType,
        targetIntensity,
        estimatedDuration: parseInt(estimatedDuration),
        scheduledDate: scheduledDate.format('YYYY-MM-DD'),
      })
      setSnackbar({ open: true, message: '创建成功', severity: 'success' })
      setCreateOpen(false)
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '创建失败', severity: 'error' })
    }
  }

  const handleCompletePlan = async () => {
    if (!selectedPlanId) return

    try {
      await trainingApi.completePlan(selectedPlanId, {
        actualDuration: parseInt(actualDuration),
        actualIntensity,
        caloriesBurned: parseInt(caloriesBurned),
      })
      setSnackbar({ open: true, message: '完成记录成功', severity: 'success' })
      setCompleteOpen(false)
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '记录失败', severity: 'error' })
    }
  }

  const handleDeletePlan = async (planId: number) => {
    try {
      await trainingApi.deletePlan(planId)
      setSnackbar({ open: true, message: '删除成功', severity: 'success' })
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '删除失败', severity: 'error' })
    }
  }

  const getProgressPercent = () => {
    if (!weeklyStats || weeklyStats.weeklyCount === 0) return 0
    return Math.round((weeklyStats.completedCount / weeklyStats.weeklyCount) * 100)
  }

  const getTypeChip = (type: string) => {
    const colors: Record<string, 'warning' | 'success' | 'info'> = {
      strength: 'warning', cardio: 'success', flexibility: 'info',
    }
    const labels: Record<string, string> = { strength: '力量', cardio: '有氧', flexibility: '柔韧' }
    return <Chip label={labels[type] || type} color={colors[type] || 'default'} size="small" />
  }

  const getIntensityChip = (intensity: string) => {
    const colors: Record<string, 'info' | 'warning' | 'error'> = {
      low: 'info', medium: 'warning', high: 'error',
    }
    return <Chip label={intensity} color={colors[intensity] || 'default'} size="small" />
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h4" gutterBottom>🔥 训练计划</Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">本周训练</Typography>
                <Typography variant="h4" color="success.main">{weeklyStats?.weeklyCount || 0} 次</Typography>
              </>}
            </CardContent></Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">本周时长</Typography>
                <Typography variant="h4">{weeklyStats?.weeklyHours || 0} 小时</Typography>
              </>}
            </CardContent></Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">消耗热量</Typography>
                <Typography variant="h4">{weeklyStats?.weeklyCalories || 0} kcal</Typography>
              </>}
            </CardContent></Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">连续训练</Typography>
                <Typography variant="h4" color="secondary.main">{weeklyStats?.streakDays || 0} 天</Typography>
              </>}
            </CardContent></Card>
          </Grid>
        </Grid>

        <Card sx={{ mt: 3 }}><CardContent>
          <Typography variant="h6" gutterBottom>本周进度</Typography>
          <LinearProgress variant="determinate" value={getProgressPercent()} color="success" />
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            {weekDays.map((day, idx) => {
              const daySchedule = schedule.filter(s => s.dayOfWeek === idx + 1)
              const completed = daySchedule.some(s => s.status === 'completed')
              return <Box key={day} sx={{ textAlign: 'center' }}>
                <Typography variant="caption">{day}</Typography>
                <Avatar sx={{ bgcolor: completed ? 'success.main' : 'grey.300', width: 32, height: 32 }}>
                  {completed ? '✓' : idx + 1}
                </Avatar>
              </Box>
            })}
          </Box>
        </CardContent></Card>

        <Card sx={{ mt: 3 }}><CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">本周训练安排</Typography>
            <Button variant="contained" onClick={() => setCreateOpen(true)}>新建计划</Button>
          </Box>
          <List>
            {schedule.map(item => (
              <ListItem key={item.planId}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: item.status === 'completed' ? 'success.main' : 'primary.main' }}>
                    {item.status === 'completed' ? '✓' : item.dayOfWeek}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText primary={item.planName} secondary={`${item.duration}分钟 · ${item.intensity}强度`} />
                <Box sx={{ display: 'flex', gap: 1 }}>
                  {getTypeChip(item.planType)}
                  {getIntensityChip(item.intensity)}
                  <Chip label={item.status === 'completed' ? '已完成' : '待完成'} color={item.status === 'completed' ? 'success' : 'primary'} size="small" />
                  {item.status === 'pending' && <>
                    <Button size="small" variant="contained" color="success" onClick={() => { setSelectedPlanId(item.planId || 0); setCompleteOpen(true) }}>完成</Button>
                    <Button size="small" variant="outlined" color="error" onClick={() => handleDeletePlan(item.planId || 0)}>删除</Button>
                  </>}
                </Box>
              </ListItem>
            ))}
          </List>
        </CardContent></Card>

        <Card sx={{ mt: 3 }}><CardContent>
          <Typography variant="h6" gutterBottom>推荐训练</Typography>
          <Grid container spacing={2}>
            {recommendations.map(item => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={item.recommendId}>
                <Card variant="outlined"><CardContent>
                  <Typography variant="subtitle1">{item.planName}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                    {getTypeChip(item.planType)}
                    {getIntensityChip(item.intensity)}
                  </Box>
                  <Typography variant="body2" color="text.secondary">{item.duration}分钟</Typography>
                  {item.caloriesBurn && <Typography variant="body2" color="text.secondary">消耗 {item.caloriesBurn} kcal</Typography>}
                </CardContent></Card>
              </Grid>
            ))}
          </Grid>
        </CardContent></Card>

        <Dialog open={createOpen} onClose={() => setCreateOpen(false)}>
          <DialogTitle>创建训练计划</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <TextField label="计划名称" value={planName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPlanName(e.target.value)} />
              <FormControl fullWidth>
                <InputLabel>训练类型</InputLabel>
                <Select value={planType} onChange={(e) => setPlanType(e.target.value)}>
                  {planTypes.map(t => <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>)}
                </Select>
              </FormControl>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControl fullWidth>
                    <InputLabel>目标强度</InputLabel>
                    <Select value={targetIntensity} onChange={(e) => setTargetIntensity(e.target.value)}>
                      {intensities.map(i => <MenuItem key={i.value} value={i.value}>{i.label}</MenuItem>)}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <TextField label="预计时长" type="number" value={estimatedDuration} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEstimatedDuration(e.target.value)} />
                </Grid>
              </Grid>
              <DatePicker label="计划日期" value={scheduledDate} onChange={(val: dayjs.Dayjs | null) => setScheduledDate(val)} />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleCreatePlan}>创建</Button>
          </DialogActions>
        </Dialog>

        <Dialog open={completeOpen} onClose={() => setCompleteOpen(false)}>
          <DialogTitle>完成训练</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <TextField label="实际时长" type="number" value={actualDuration} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setActualDuration(e.target.value)} />
              <FormControl fullWidth>
                <InputLabel>实际强度</InputLabel>
                <Select value={actualIntensity} onChange={(e) => setActualIntensity(e.target.value)}>
                  {intensities.map(i => <MenuItem key={i.value} value={i.value}>{i.label}</MenuItem>)}
                </Select>
              </FormControl>
              <TextField label="消耗热量" type="number" value={caloriesBurned} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCaloriesBurned(e.target.value)} />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCompleteOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleCompletePlan}>提交</Button>
          </DialogActions>
        </Dialog>

        <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
        </Snackbar>
      </Box>
    </LocalizationProvider>
  )
}

export default Training