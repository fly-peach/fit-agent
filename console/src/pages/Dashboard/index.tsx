import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Grid,
  Skeleton,
} from '@mui/material'
import {
  Favorite as HealthIcon,
  LocalFireDepartment as FireIcon,
  EmojiEvents as TrophyIcon,
  Restaurant as DietIcon,
} from '@mui/icons-material'
import { healthApi, type HealthMetrics } from '../../services/health'
import { trainingApi, type WeeklyStats, TrainingSchedule } from '../../services/training'
import { dietApi, type DietStats } from '../../services/diet'

const Dashboard: React.FC = () => {
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null)
  const [weeklyStats, setWeeklyStats] = useState<WeeklyStats | null>(null)
  const [dietStats, setDietStats] = useState<DietStats | null>(null)
  const [schedule, setSchedule] = useState<TrainingSchedule[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [health, stats, diet, sched] = await Promise.all([
        healthApi.getMetrics(),
        trainingApi.getWeeklyStats(),
        dietApi.getTodayStats(),
        trainingApi.getWeeklySchedule(),
      ])
      setHealthMetrics(health)
      setWeeklyStats(stats)
      setDietStats(diet)
      setSchedule(sched)
    } finally {
      setLoading(false)
    }
  }

  const getProgressPercent = (current: number, goal: number) => {
    if (!goal) return 0
    return Math.round((current / goal) * 100)
  }

  const getTypeChip = (type: string) => {
    const colors: Record<string, 'warning' | 'success' | 'info'> = {
      strength: 'warning',
      cardio: 'success',
      flexibility: 'info',
    }
    const labels: Record<string, string> = {
      strength: '力量',
      cardio: '有氧',
      flexibility: '柔韧',
    }
    return <Chip label={labels[type] || type} color={colors[type] || 'default'} size="small" />
  }

  const getStatusChip = (status: string) => {
    if (status === 'completed') return <Chip label="已完成" color="success" size="small" />
    return <Chip label="待完成" color="primary" size="small" />
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        📊 今日概览
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              {loading ? <Skeleton width={100} /> : (
                <>
                  <Typography color="text.secondary" gutterBottom>
                    <FireIcon sx={{ mr: 1 }} /> 本周训练
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {weeklyStats?.weeklyCount || 0} 次
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={weeklyStats ? getProgressPercent(weeklyStats.completedCount, weeklyStats.weeklyCount) : 0}
                    color="success"
                    sx={{ mt: 1 }}
                  />
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              {loading ? <Skeleton width={100} /> : (
                <>
                  <Typography color="text.secondary" gutterBottom>
                    <DietIcon sx={{ mr: 1 }} /> 今日卡路里
                  </Typography>
                  <Typography variant="h4" color="error.main">
                    {dietStats?.remainingCalories || 0} kcal
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    已摄入 {dietStats?.calories || 0} / {dietStats?.caloriesGoal || 2000} kcal
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              {loading ? <Skeleton width={100} /> : (
                <>
                  <Typography color="text.secondary" gutterBottom>
                    <TrophyIcon sx={{ mr: 1 }} /> 连续训练
                  </Typography>
                  <Typography variant="h4" color="secondary.main">
                    {weeklyStats?.streakDays || 0} 天
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    继续保持！
                  </Typography>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              {loading ? <Skeleton width={100} /> : (
                <>
                  <Typography color="text.secondary" gutterBottom>
                    <HealthIcon sx={{ mr: 1 }} /> 当前体重
                  </Typography>
                  <Typography variant="h4">
                    {healthMetrics?.weight || 0} kg
                  </Typography>
                  {healthMetrics?.weightGoal && (
                    <Typography variant="body2" color="text.secondary">
                      目标 {healthMetrics.weightGoal} kg
                    </Typography>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 2 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                本周训练安排
              </Typography>
              <List>
                {(loading ? [] : schedule).slice(0, 5).map((item) => (
                  <ListItem key={item.planId}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: item.status === 'completed' ? 'success.main' : 'primary.main' }}>
                        {item.status === 'completed' ? '✓' : item.dayOfWeek}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={item.planName}
                      secondary={`${item.duration}分钟 · ${item.intensity}强度`}
                    />
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {getTypeChip(item.planType)}
                      {getStatusChip(item.status)}
                    </Box>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                今日营养摄入
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">蛋白质</Typography>
                <LinearProgress
                  variant="determinate"
                  value={getProgressPercent(dietStats?.protein || 0, dietStats?.proteinGoal || 150)}
                  color="success"
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2">碳水</Typography>
                <LinearProgress
                  variant="determinate"
                  value={getProgressPercent(dietStats?.carbs || 0, dietStats?.carbsGoal || 250)}
                  color="warning"
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2">脂肪</Typography>
                <LinearProgress
                  variant="determinate"
                  value={getProgressPercent(dietStats?.fat || 0, dietStats?.fatGoal || 65)}
                  color="error"
                  sx={{ mb: 2 }}
                />
                <Typography variant="body2">饮水</Typography>
                <LinearProgress
                  variant="determinate"
                  value={getProgressPercent(dietStats?.water || 0, dietStats?.waterGoal || 2000)}
                  color="info"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Dashboard