import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  LinearProgress,
  Chip,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Snackbar,
  Alert,
  Skeleton,
} from '@mui/material'
import { TimePicker } from '@mui/x-date-pickers/TimePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs from 'dayjs'
import { dietApi, type DietStats, DietMeal, RecommendedFood } from '../../services/diet'

const mealTypes = [
  { value: 'breakfast', label: '早餐' },
  { value: 'lunch', label: '午餐' },
  { value: 'dinner', label: '晚餐' },
  { value: 'snack', label: '加餐' },
]

const Diet: React.FC = () => {
  const [stats, setStats] = useState<DietStats | null>(null)
  const [meals, setMeals] = useState<DietMeal[]>([])
  const [recommendations, setRecommendations] = useState<RecommendedFood[]>([])
  const [loading, setLoading] = useState(true)
  const [addOpen, setAddOpen] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [selectedMeal, setSelectedMeal] = useState<DietMeal | null>(null)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success'
  })

  const [mealType, setMealType] = useState('breakfast')
  const [mealName, setMealName] = useState('')
  const [calories, setCalories] = useState('0')
  const [protein, setProtein] = useState('0')
  const [carbs, setCarbs] = useState('0')
  const [fat, setFat] = useState('0')
  const [water, setWater] = useState('0')
  const [time, setTime] = useState<dayjs.Dayjs | null>(dayjs())

  const [editMealName, setEditMealName] = useState('')
  const [editCalories, setEditCalories] = useState('0')
  const [editProtein, setEditProtein] = useState('0')
  const [editCarbs, setEditCarbs] = useState('0')
  const [editFat, setEditFat] = useState('0')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsData, mealsData, recs] = await Promise.all([
        dietApi.getTodayStats(),
        dietApi.getTodayMeals(),
        dietApi.getRecommendations(),
      ])
      setStats(statsData)
      setMeals(mealsData)
      setRecommendations(recs)
    } finally {
      setLoading(false)
    }
  }

  const handleAddMeal = async () => {
    if (!mealName || !calories || !time) {
      setSnackbar({ open: true, message: '请填写必要字段', severity: 'error' })
      return
    }

    try {
      await dietApi.createMeal({
        mealType,
        mealName,
        calories: parseInt(calories),
        protein: parseInt(protein),
        carbs: parseInt(carbs),
        fat: parseInt(fat),
        water: parseInt(water),
        time: time.format('HH:mm'),
      })
      setSnackbar({ open: true, message: '添加成功', severity: 'success' })
      setAddOpen(false)
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '添加失败', severity: 'error' })
    }
  }

  const handleEditMeal = async () => {
    if (!selectedMeal) return

    try {
      await dietApi.updateMeal(selectedMeal.mealId, {
        mealName: editMealName,
        calories: parseInt(editCalories),
        protein: parseInt(editProtein),
        carbs: parseInt(editCarbs),
        fat: parseInt(editFat),
      })
      setSnackbar({ open: true, message: '更新成功', severity: 'success' })
      setEditOpen(false)
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '更新失败', severity: 'error' })
    }
  }

  const handleDeleteMeal = async (mealId: number) => {
    try {
      await dietApi.deleteMeal(mealId)
      setSnackbar({ open: true, message: '删除成功', severity: 'success' })
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '删除失败', severity: 'error' })
    }
  }

  const openEditDialog = (meal: DietMeal) => {
    setSelectedMeal(meal)
    setEditMealName(meal.mealName)
    setEditCalories(String(meal.calories))
    setEditProtein(String(meal.protein))
    setEditCarbs(String(meal.carbs))
    setEditFat(String(meal.fat))
    setEditOpen(true)
  }

  const getProgressPercent = (current: number, goal: number) => {
    if (!goal) return 0
    return Math.round((current / goal) * 100)
  }

  const getMealTypeChip = (type: string) => {
    const colors: Record<string, 'warning' | 'success' | 'info' | 'secondary'> = {
      breakfast: 'warning', lunch: 'success', dinner: 'info', snack: 'secondary',
    }
    const labels: Record<string, string> = { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }
    return <Chip label={labels[type] || type} color={colors[type] || 'default'} size="small" />
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h4" gutterBottom>🍽️ 饮食管理</Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={4}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">今日热量</Typography>
                <Typography variant="h4" color="error.main">{stats?.calories || 0} / {stats?.caloriesGoal || 2000} kcal</Typography>
                <LinearProgress variant="determinate" value={getProgressPercent(stats?.calories || 0, stats?.caloriesGoal || 2000)} color="success" />
                <Typography variant="body2" color="text.secondary">剩余 {stats?.remainingCalories || 0} kcal</Typography>
              </>}
            </CardContent></Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">连续记录</Typography>
                <Typography variant="h4">{stats?.streakDays || 0} 天</Typography>
              </>}
            </CardContent></Card>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Card><CardContent>
              {loading ? <Skeleton /> : <>
                <Typography color="text.secondary">饮水</Typography>
                <Typography variant="h4">{stats?.water || 0} / {stats?.waterGoal || 2000} ml</Typography>
                <LinearProgress variant="determinate" value={getProgressPercent(stats?.water || 0, stats?.waterGoal || 2000)} color="info" />
              </>}
            </CardContent></Card>
          </Grid>
        </Grid>

        <Card sx={{ mt: 3 }}><CardContent>
          <Typography variant="h6" gutterBottom>今日营养摄入</Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <Typography variant="body2">蛋白质</Typography>
              <LinearProgress variant="determinate" value={getProgressPercent(stats?.protein || 0, stats?.proteinGoal || 150)} color="success" />
              <Typography variant="caption">{stats?.protein || 0}/{stats?.proteinGoal || 150}g</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2">碳水</Typography>
              <LinearProgress variant="determinate" value={getProgressPercent(stats?.carbs || 0, stats?.carbsGoal || 250)} color="warning" />
              <Typography variant="caption">{stats?.carbs || 0}/{stats?.carbsGoal || 250}g</Typography>
            </Grid>
            <Grid item xs={4}>
              <Typography variant="body2">脂肪</Typography>
              <LinearProgress variant="determinate" value={getProgressPercent(stats?.fat || 0, stats?.fatGoal || 65)} color="error" />
              <Typography variant="caption">{stats?.fat || 0}/{stats?.fatGoal || 65}g</Typography>
            </Grid>
          </Grid>
        </CardContent></Card>

        <Card sx={{ mt: 3 }}><CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
            <Typography variant="h6">今日饮食记录</Typography>
            <Button variant="contained" onClick={() => setAddOpen(true)}>添加记录</Button>
          </Box>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>类型</TableCell>
                  <TableCell>食物</TableCell>
                  <TableCell>热量</TableCell>
                  <TableCell>蛋白质</TableCell>
                  <TableCell>碳水</TableCell>
                  <TableCell>脂肪</TableCell>
                  <TableCell>时间</TableCell>
                  <TableCell>操作</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {meals.map(m => (
                  <TableRow key={m.mealId}>
                    <TableCell>{getMealTypeChip(m.mealType)}</TableCell>
                    <TableCell>{m.mealName}</TableCell>
                    <TableCell>{m.calories} kcal</TableCell>
                    <TableCell>{m.protein}g</TableCell>
                    <TableCell>{m.carbs}g</TableCell>
                    <TableCell>{m.fat}g</TableCell>
                    <TableCell>{m.time}</TableCell>
                    <TableCell>
                      <Button size="small" onClick={() => openEditDialog(m)}>编辑</Button>
                      <Button size="small" color="error" onClick={() => handleDeleteMeal(m.mealId)}>删除</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent></Card>

        <Card sx={{ mt: 3 }}><CardContent>
          <Typography variant="h6" gutterBottom>推荐食物</Typography>
          <Grid container spacing={2}>
            {recommendations.map(item => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={item.recommendId}>
                <Card variant="outlined"><CardContent>
                  <Typography variant="subtitle1">{item.foodName}</Typography>
                  <Typography variant="body2" color="text.secondary">{item.calories} kcal</Typography>
                  {item.protein && <Typography variant="caption">{item.protein}g蛋白质</Typography>}
                  {item.reason && <Chip label={item.reason} color="primary" size="small" sx={{ mt: 1 }} />}
                </CardContent></Card>
              </Grid>
            ))}
          </Grid>
        </CardContent></Card>

        <Dialog open={addOpen} onClose={() => setAddOpen(false)}>
          <DialogTitle>添加饮食记录</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <FormControl fullWidth><InputLabel>餐次类型</InputLabel>
                <Select value={mealType} onChange={(e) => setMealType(e.target.value)}>
                  {mealTypes.map(m => <MenuItem key={m.value} value={m.value}>{m.label}</MenuItem>)}
                </Select>
              </FormControl>
              <TextField label="食物名称" value={mealName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setMealName(e.target.value)} />
              <Grid container spacing={2}>
                <Grid item xs={6}><TextField label="热量" type="number" value={calories} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCalories(e.target.value)} /></Grid>
                <Grid item xs={6}><TextField label="蛋白质" type="number" value={protein} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setProtein(e.target.value)} /></Grid>
              </Grid>
              <Grid container spacing={2}>
                <Grid item xs={6}><TextField label="碳水" type="number" value={carbs} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setCarbs(e.target.value)} /></Grid>
                <Grid item xs={6}><TextField label="脂肪" type="number" value={fat} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFat(e.target.value)} /></Grid>
              </Grid>
              <TextField label="饮水" type="number" value={water} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWater(e.target.value)} />
              <TimePicker label="时间" value={time} onChange={(val: dayjs.Dayjs | null) => setTime(val)} />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleAddMeal}>提交</Button>
          </DialogActions>
        </Dialog>

        <Dialog open={editOpen} onClose={() => setEditOpen(false)}>
          <DialogTitle>编辑饮食记录</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <TextField label="食物名称" value={editMealName} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditMealName(e.target.value)} />
              <TextField label="热量" type="number" value={editCalories} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditCalories(e.target.value)} />
              <TextField label="蛋白质" type="number" value={editProtein} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditProtein(e.target.value)} />
              <TextField label="碳水" type="number" value={editCarbs} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditCarbs(e.target.value)} />
              <TextField label="脂肪" type="number" value={editFat} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setEditFat(e.target.value)} />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setEditOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleEditMeal}>更新</Button>
          </DialogActions>
        </Dialog>

        <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
        </Snackbar>
      </Box>
    </LocalizationProvider>
  )
}

export default Diet