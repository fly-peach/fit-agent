import React, { useEffect, useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Skeleton,
  Snackbar,
  Alert,
} from '@mui/material'
import { DatePicker } from '@mui/x-date-pickers/DatePicker'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import dayjs from 'dayjs'
import { healthApi, type HealthMetrics, HealthMeasurement, HealthReport } from '../../services/health'

const Health: React.FC = () => {
  const [metrics, setMetrics] = useState<HealthMetrics | null>(null)
  const [measurements, setMeasurements] = useState<HealthMeasurement[]>([])
  const [report, setReport] = useState<HealthReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false, message: '', severity: 'success'
  })

  const [weight, setWeight] = useState('70')
  const [height, setHeight] = useState('175')
  const [bodyFat, setBodyFat] = useState('15')
  const [measureDate, setMeasureDate] = useState<dayjs.Dayjs | null>(dayjs())

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [metricsData, measurementsData, reportData] = await Promise.all([
        healthApi.getMetrics(),
        healthApi.getMeasurements(20),
        healthApi.getReport('week'),
      ])
      setMetrics(metricsData)
      setMeasurements(measurementsData)
      setReport(reportData)
    } finally {
      setLoading(false)
    }
  }

  const handleAddRecord = async () => {
    if (!weight || !height || !bodyFat || !measureDate) {
      setSnackbar({ open: true, message: '请填写所有字段', severity: 'error' })
      return
    }

    try {
      await healthApi.createMetric({
        weight: parseFloat(weight),
        height: parseFloat(height),
        bodyFat: parseFloat(bodyFat),
        measureDate: measureDate.format('YYYY-MM-DD'),
      })
      setSnackbar({ open: true, message: '记录成功', severity: 'success' })
      setModalOpen(false)
      fetchData()
    } catch {
      setSnackbar({ open: true, message: '记录失败', severity: 'error' })
    }
  }

  const handleExport = async () => {
    try {
      const blob = await healthApi.exportData('week', 'csv') as unknown as Blob
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'health_data.csv'
      a.click()
      window.URL.revokeObjectURL(url)
      setSnackbar({ open: true, message: '导出成功', severity: 'success' })
    } catch {
      setSnackbar({ open: true, message: '导出失败', severity: 'error' })
    }
  }

  const getBmiStatusChip = (status: string) => {
    const colors: Record<string, 'success' | 'info' | 'warning' | 'default'> = {
      normal: 'success',
      under: 'info',
      over: 'warning',
    }
    const labels: Record<string, string> = { normal: '正常', under: '偏瘦', over: '偏胖' }
    return <Chip label={labels[status] || status} color={colors[status] || 'default'} size="small" />
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box>
        <Typography variant="h4" gutterBottom>
          ❤️ 健康数据
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                {loading ? <Skeleton /> : (
                  <>
                    <Typography color="text.secondary">当前体重</Typography>
                    <Typography variant="h4">{metrics?.weight || 0} kg</Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                {loading ? <Skeleton /> : (
                  <>
                    <Typography color="text.secondary">身高</Typography>
                    <Typography variant="h4">{metrics?.height || 175} cm</Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                {loading ? <Skeleton /> : (
                  <>
                    <Typography color="text.secondary">体脂率</Typography>
                    <Typography variant="h4">{metrics?.bodyFat || 0}%</Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                {loading ? <Skeleton /> : (
                  <>
                    <Typography color="text.secondary">BMI</Typography>
                    <Typography variant="h4">{metrics?.bmi?.toFixed(1) || 0}</Typography>
                    {metrics?.bmiStatus && getBmiStatusChip(metrics.bmiStatus)}
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">历史记录</Typography>
              <Box>
                <Button variant="contained" onClick={() => setModalOpen(true)} sx={{ mr: 1 }}>
                  添加记录
                </Button>
                <Button variant="outlined" onClick={handleExport}>导出</Button>
              </Box>
            </Box>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>日期</TableCell>
                    <TableCell>体重</TableCell>
                    <TableCell>体脂率</TableCell>
                    <TableCell>BMI</TableCell>
                    <TableCell>状态</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {measurements.map((m) => (
                    <TableRow key={m.recordId}>
                      <TableCell>{dayjs(m.measureDate).format('YYYY-MM-DD')}</TableCell>
                      <TableCell>{m.weight} kg</TableCell>
                      <TableCell>{m.bodyFat}%</TableCell>
                      <TableCell>{m.bmi.toFixed(1)}</TableCell>
                      <TableCell>{getBmiStatusChip(m.bmiStatus)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>

        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>📈 健康趋势</Typography>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="subtitle1">体重变化</Typography>
                {report?.weightTrend?.map((item, idx) => (
                  <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                    <Typography>{dayjs(item.date).format('MM-DD')}</Typography>
                    <Typography>{item.value} kg</Typography>
                  </Box>
                ))}
                {report?.summary && (
                  <Typography color="text.secondary" sx={{ mt: 1 }}>
                    平均: {report.summary.avgWeight} kg · 变化: {report.summary.weightChange > 0 ? '+' : ''}{report.summary.weightChange} kg
                  </Typography>
                )}
              </Grid>
              <Grid item xs={6}>
                <Typography variant="subtitle1">BMI变化</Typography>
                {report?.bmiTrend?.map((item, idx) => (
                  <Box key={idx} sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                    <Typography>{dayjs(item.date).format('MM-DD')}</Typography>
                    <Typography>{item.value.toFixed(1)}</Typography>
                  </Box>
                ))}
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        <Dialog open={modalOpen} onClose={() => setModalOpen(false)}>
          <DialogTitle>添加健康记录</DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
              <TextField label="体重 (kg)" type="number" value={weight} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setWeight(e.target.value)} />
              <TextField label="身高 (cm)" type="number" value={height} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setHeight(e.target.value)} />
              <TextField label="体脂率 (%)" type="number" value={bodyFat} onChange={(e: React.ChangeEvent<HTMLInputElement>) => setBodyFat(e.target.value)} />
              <DatePicker label="测量日期" value={measureDate} onChange={(val: dayjs.Dayjs | null) => setMeasureDate(val)} />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setModalOpen(false)}>取消</Button>
            <Button variant="contained" onClick={handleAddRecord}>提交</Button>
          </DialogActions>
        </Dialog>

        <Snackbar open={snackbar.open} autoHideDuration={3000} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          <Alert severity={snackbar.severity}>{snackbar.message}</Alert>
        </Snackbar>
      </Box>
    </LocalizationProvider>
  )
}

export default Health