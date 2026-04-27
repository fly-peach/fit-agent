import React from 'react'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
  Divider,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Favorite as HealthIcon,
  FitnessCenter as TrainingIcon,
  Restaurant as DietIcon,
  Person as UserIcon,
  Logout as LogoutIcon,
  Menu as MenuIcon,
  ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon,
} from '@mui/icons-material'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const drawerWidth = 240
const drawerClosedWidth = 0
const rightDrawerWidth = '30vw'

const menuItems = [
  { path: '/', label: '概览', icon: <DashboardIcon /> },
  { path: '/health', label: '健康数据', icon: <HealthIcon /> },
  { path: '/training', label: '训练计划', icon: <TrainingIcon /> },
  { path: '/diet', label: '饮食管理', icon: <DietIcon /> },
  { path: '/user', label: '个人中心', icon: <UserIcon /> },
]

const MainLayout: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null)
  const [sidebarOpen, setSidebarOpen] = React.useState(true)
  const [rightDrawerOpen, setRightDrawerOpen] = React.useState(false)

  const toggleSidebar = () => {
    setSidebarOpen((prev) => !prev)
  }

  const toggleRightDrawer = () => {
    setRightDrawerOpen((prev) => !prev)
  }

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          left: sidebarOpen ? `${drawerWidth}px` : 0,
          right: rightDrawerOpen ? rightDrawerWidth : 0,
          width: 'auto',
          transition: theme =>
            theme.transitions.create(['left', 'right'], {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="toggle sidebar"
            onClick={toggleSidebar}
            sx={{ mr: 2 }}
          >
            {sidebarOpen ? <ChevronLeftIcon /> : <MenuIcon />}
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find((m) => m.path === location.pathname)?.label || '概览'}
          </Typography>
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenu}
            color="inherit"
          >
            <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
              {user.name?.charAt(0) || 'U'}
            </Avatar>
          </IconButton>
          <IconButton
            color="inherit"
            aria-label="toggle right sidebar"
            onClick={toggleRightDrawer}
            sx={{ ml: 1, px: 1.5, py: 0.5, borderRadius: 2, border: '1px solid rgba(255,255,255,0.3)', textTransform: 'none', fontSize: '0.875rem' }}
          >
            AI助手
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={() => { handleClose(); navigate('/user') }}>
              <ListItemIcon>
                <UserIcon fontSize="small" />
              </ListItemIcon>
              个人中心
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              退出登录
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="persistent"
        anchor="left"
        open={sidebarOpen}
        sx={{
          width: sidebarOpen ? drawerWidth : drawerClosedWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            transition: theme =>
              theme.transitions.create(['width', 'transform'], {
                easing: theme.transitions.easing.easeInOut,
                duration: theme.transitions.duration.enteringScreen,
              }),
            overflowX: 'hidden',
            ...(sidebarOpen ? {} : {
              transform: `translateX(-${drawerWidth}px)`,
              width: 0,
            }),
          },
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" color="primary">
            FitAgent
          </Typography>
        </Toolbar>
        <Divider />
        <List>
          {menuItems.map((item) => (
            <ListItem key={item.path} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.label} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: 'background.default',
          p: 3,
          minWidth: 0,
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
      <Drawer
        variant="persistent"
        anchor="right"
        open={rightDrawerOpen}
        sx={{
          width: rightDrawerOpen ? rightDrawerWidth : drawerClosedWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: rightDrawerWidth,
            minWidth: rightDrawerWidth,
            boxSizing: 'border-box',
            transition: theme =>
              theme.transitions.create(['width', 'transform'], {
                easing: theme.transitions.easing.easeInOut,
                duration: theme.transitions.duration.enteringScreen,
              }),
            overflowX: 'hidden',
            ...(rightDrawerOpen ? {} : {
              transform: `translateX(${rightDrawerWidth})`,
              width: 0,
            }),
          },
        }}
      >
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography variant="h6" noWrap component="div" color="primary">
            AI助手
          </Typography>
          <IconButton onClick={toggleRightDrawer} size="small">
            <ChevronRightIcon />
          </IconButton>
        </Toolbar>
        <Divider />
        <Box sx={{ p: 2 }}>
          <Typography variant="body2" color="text.secondary">
            AI 助手面板
          </Typography>
        </Box>
      </Drawer>
    </Box>
  )
}

export default MainLayout