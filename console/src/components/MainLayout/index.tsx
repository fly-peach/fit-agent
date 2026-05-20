import React, { useState, useEffect, useRef, useCallback } from "react";
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Button,
  Typography,
  Drawer,
} from "antd";
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DownOutlined,
  UserOutlined,
  LogoutOutlined,
} from "@ant-design/icons";
import {
  LayoutDashboard,
  Heart,
  Dumbbell,
  Utensils,
  User,
  Bot,
  BarChart4,
} from "lucide-react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import type { MenuProps } from "antd";
import AIAssistant from "../AIAssistant";
import BottomSheet from "../BottomSheet";
import { useIsMobile } from "../../hooks";
import {
  OPEN_CARD_GENERATION_EVENT,
  startCardGeneration,
  type CardGenerationRequestDetail,
} from "../AIAssistant/bridge";

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const IconWrapper: React.FC<{
  children: React.ReactNode;
  color: string;
  collapsed?: boolean;
}> = ({ children, color, collapsed }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      width: collapsed ? 36 : 32,
      height: collapsed ? 36 : 32,
      borderRadius: 10,
      background: `${color}15`,
      color,
      fontSize: 16,
      transition: "all 0.2s ease",
    }}
  >
    {children}
  </span>
);

const navItems = [
  { key: "/", icon: LayoutDashboard, label: "概览", color: "#0EA5E9" },
  { key: "/health", icon: Heart, label: "健康数据", color: "#10B981" },
  { key: "/training", icon: Dumbbell, label: "训练计划", color: "#F59E0B" },
  { key: "/diet", icon: Utensils, label: "饮食管理", color: "#06B6D4" },
  { key: "/agent-config", icon: Bot, label: "Agent 配置", color: "#8B5CF6" },
  {
    key: "personal",
    icon: User,
    label: "个人中心",
    color: "#8B5CF6",
    children: [
      { key: "/user", icon: User, label: "个人设置", color: "#8B5CF6" },
      { key: "/training-results", icon: BarChart4, label: "训练成果", color: "#F59E0B" },
    ]
  },
];

const getMenuItems = (collapsed: boolean): MenuProps["items"] =>
  navItems.map((item) => {
    if ('children' in item) {
      return {
        key: item.key,
        icon: (
          <IconWrapper color={item.color} collapsed={collapsed}>
            <item.icon size={16} />
          </IconWrapper>
        ),
        label: item.label,
        children: (item.children ?? []).map((child: any) => ({
          key: child.key,
          icon: (
            <IconWrapper color={child.color} collapsed={collapsed}>
              <child.icon size={16} />
            </IconWrapper>
          ),
          label: child.label,
        })),
      };
    }
    return {
      key: item.key,
      icon: (
        <IconWrapper color={item.color} collapsed={collapsed}>
          <item.icon size={16} />
        </IconWrapper>
      ),
      label: item.label,
    };
  });

// Mobile bottom nav icons (no wrapper for compactness)
const mobileNavItems = [
  {
    key: "/",
    icon: <LayoutDashboard size={20} />,
    label: "概览",
    color: "#0EA5E9",
  },
  {
    key: "/health",
    icon: <Heart size={20} />,
    label: "健康",
    color: "#10B981",
  },
  {
    key: "/training",
    icon: <Dumbbell size={20} />,
    label: "训练",
    color: "#F59E0B",
  },
  {
    key: "/diet",
    icon: <Utensils size={20} />,
    label: "饮食",
    color: "#06B6D4",
  },
  { key: "/user", icon: <User size={20} />, label: "我的", color: "#8B5CF6" },
];

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const [collapsed, setCollapsed] = useState(false);
  const [rightDrawerOpen, setRightDrawerOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isMobile = useIsMobile();

  // Resizable sidebar state
  const [aiPanelWidth, setAiPanelWidth] = useState(() => {
    const saved = localStorage.getItem("aiPanelWidth");
    return saved ? parseInt(saved, 10) : 480;
  });
  const [isDragging, setIsDragging] = useState(false);
  const [pendingCardGeneration, setPendingCardGeneration] = useState<CardGenerationRequestDetail | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragStartXRef = useRef(0);
  const dragStartWidthRef = useRef(0);

  // Calculate dynamic min/max based on window width
  const getDynamicConstraints = useCallback(() => {
    const windowWidth = window.innerWidth;
    const sidebarWidth = collapsed ? 72 : 240;
    const availableWidth = windowWidth - sidebarWidth;
    const MIN_AI_PANEL_WIDTH = Math.min(360, availableWidth - 100);
    const MAX_AI_PANEL_WIDTH = Math.max(500, Math.min(800, availableWidth - 100));
    return { MIN_AI_PANEL_WIDTH, MAX_AI_PANEL_WIDTH, availableWidth };
  }, [collapsed]);

  // Adjust width when window resizes or when opening
  useEffect(() => {
    if (rightDrawerOpen) {
      const { MIN_AI_PANEL_WIDTH, MAX_AI_PANEL_WIDTH, availableWidth } = getDynamicConstraints();
      setAiPanelWidth(prev => {
        const clamped = Math.max(MIN_AI_PANEL_WIDTH, Math.min(MAX_AI_PANEL_WIDTH, prev, availableWidth - 50));
        return clamped;
      });
    }
  }, [rightDrawerOpen, getDynamicConstraints]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (rightDrawerOpen) {
        const { MIN_AI_PANEL_WIDTH, MAX_AI_PANEL_WIDTH, availableWidth } = getDynamicConstraints();
        setAiPanelWidth(prev => {
          const clamped = Math.max(MIN_AI_PANEL_WIDTH, Math.min(MAX_AI_PANEL_WIDTH, prev, availableWidth - 50));
          return clamped;
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [rightDrawerOpen, getDynamicConstraints]);

  // Save width to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("aiPanelWidth", aiPanelWidth.toString());
  }, [aiPanelWidth]);

  useEffect(() => {
    const handleOpenCardGeneration = (event: Event) => {
      const detail = (event as CustomEvent<CardGenerationRequestDetail>).detail;
      if (!detail) return;
      setPendingCardGeneration(detail);
      setRightDrawerOpen(true);
    };

    window.addEventListener(OPEN_CARD_GENERATION_EVENT, handleOpenCardGeneration as EventListener);
    return () => {
      window.removeEventListener(OPEN_CARD_GENERATION_EVENT, handleOpenCardGeneration as EventListener);
    };
  }, []);

  useEffect(() => {
    if (!rightDrawerOpen || !pendingCardGeneration) return;

    const timer = window.setTimeout(() => {
      startCardGeneration(pendingCardGeneration);
      setPendingCardGeneration(null);
    }, 0);

    return () => window.clearTimeout(timer);
  }, [rightDrawerOpen, pendingCardGeneration]);

  // Handle double-click to maximize width
  const handleMaxWidth = useCallback(() => {
    const { MAX_AI_PANEL_WIDTH } = getDynamicConstraints();
    setAiPanelWidth(MAX_AI_PANEL_WIDTH);
  }, [getDynamicConstraints]);

  // Handle drag start
  const handleDragStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(true);
      dragStartXRef.current = e.clientX;
      dragStartWidthRef.current = aiPanelWidth;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    },
    [aiPanelWidth],
  );

  // Handle drag move
  const handleDragMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;
      const deltaX = dragStartXRef.current - e.clientX;
      let newWidth = dragStartWidthRef.current + deltaX;
      const { MIN_AI_PANEL_WIDTH, MAX_AI_PANEL_WIDTH } = getDynamicConstraints();
      newWidth = Math.max(
        MIN_AI_PANEL_WIDTH,
        Math.min(MAX_AI_PANEL_WIDTH, newWidth),
      );
      setAiPanelWidth(newWidth);
    },
    [isDragging, getDynamicConstraints],
  );

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  }, []);

  // Add and remove global event listeners
  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleDragMove);
      window.addEventListener("mouseup", handleDragEnd);
      window.addEventListener("mouseleave", handleDragEnd);
    }
    return () => {
      window.removeEventListener("mousemove", handleDragMove);
      window.removeEventListener("mouseup", handleDragEnd);
      window.removeEventListener("mouseleave", handleDragEnd);
    };
  }, [isDragging, handleDragMove, handleDragEnd]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const userMenuItems: MenuProps["items"] = [
    {
      key: "profile",
      icon: <UserOutlined />,
      label: "个人中心",
      onClick: () => {
        navigate("/user");
        setMobileMenuOpen(false);
      },
    },
    {
      key: "logout",
      icon: <LogoutOutlined />,
      label: "退出登录",
      onClick: handleLogout,
    },
  ];

  const handleNav = (key: string) => {
    navigate(key);
    setMobileMenuOpen(false);
  };

  // Mobile bottom navigation
  if (isMobile) {
    return (
      <Layout style={{ minHeight: "100vh" }}>
        <Header
          style={{
            padding: "0 16px",
            background: "rgba(255, 255, 255, 0.95)",
            backdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 100,
            borderBottom: "1px solid #F0EDE8",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Title
              level={5}
              style={{
                margin: 0,
                color: "#0EA5E9",
                fontWeight: 800,
                fontFamily: "'Nunito', 'Noto Sans SC', sans-serif",
              }}
            >
              FitAgent
            </Title>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <Button
              type="text"
              icon={<Bot size={18} />}
              onClick={() => setRightDrawerOpen(!rightDrawerOpen)}
              size="small"
            />
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar style={{ backgroundColor: "#0EA5E9", cursor: "pointer" }}>
                {user.name?.charAt(0) || "U"}
              </Avatar>
            </Dropdown>
          </div>
        </Header>
        <Layout
          style={{
            flexDirection: "row",
            height: "calc(100vh - 56px)",
            overflow: "hidden",
          }}
        >
          <Content
            style={{
              flex: 1,
              background: "transparent",
              overflow: "auto",
              transition: "flex 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            <Outlet />
          </Content>
        </Layout>

        {/* Mobile AI Assistant Bottom Sheet */}
        <BottomSheet
          open={rightDrawerOpen}
          onClose={() => setRightDrawerOpen(false)}
          snapPoints={[280, '50%', '90%']}
          initialSnapIndex={1}
        >
          <AIAssistant />
        </BottomSheet>
        {/* Mobile bottom navigation */}
        <div
          style={{
            position: "fixed",
            bottom: 0,
            left: 0,
            right: 0,
            height: 56,
            background: "rgba(255, 255, 255, 0.98)",
            backdropFilter: "blur(12px)",
            borderTop: "1px solid #F0EDE8",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-around",
            zIndex: 100,
            paddingLeft: 4,
            paddingRight: 4,
          }}
        >
          {mobileNavItems.map((item) => (
            <div
              key={item.key}
              onClick={() => handleNav(item.key)}
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: 2,
                cursor: "pointer",
                padding: "4px 12px",
                borderRadius: 8,
                background:
                  location.pathname === item.key
                    ? `${item.color}12`
                    : "transparent",
                color: location.pathname === item.key ? item.color : "#999",
                transition: "all 0.2s",
                flex: 1,
              }}
            >
              {item.icon}
              <span style={{ fontSize: 10, lineHeight: 1 }}>{item.label}</span>
            </div>
          ))}
        </div>
      </Layout>
    );
  }

  // Desktop layout
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        collapsedWidth={72}
        width={240}
        theme="light"
        style={{
          overflow: "hidden",
          height: "100vh",
          position: "fixed",
          left: 0,
          top: 0,
          bottom: 0,
          background: "linear-gradient(180deg, #FFFFFF 0%, #F8F6F3 100%)",
          borderRight: "1px solid #F0EDE8",
          zIndex: 100,
        }}
      >
        <div
          style={{
            height: 64,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 16px",
            borderBottom: "1px solid #F0EDE8",
            transition: "all 0.2s ease",
          }}
        >
          {collapsed ? (
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 10,
                background: "linear-gradient(135deg, #0EA5E9, #06B6D4)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                flexShrink: 0,
              }}
            >
              <span
                style={{
                  color: "#fff",
                  fontWeight: 800,
                  fontSize: 16,
                  fontFamily: "'Nunito', sans-serif",
                }}
              >
                FA
              </span>
            </div>
          ) : (
            <Title
              level={4}
              style={{
                color: "#0EA5E9",
                margin: 0,
                fontWeight: 800,
                fontFamily: "'Nunito', 'Noto Sans SC', sans-serif",
                whiteSpace: "nowrap",
              }}
            >
              FitAgent
            </Title>
          )}
        </div>
        <Menu
          theme="light"
          mode="inline"
          inlineCollapsed={collapsed}
          selectedKeys={[location.pathname]}
          items={getMenuItems(collapsed)}
          onClick={({ key }) => navigate(key)}
          style={{
            borderRight: "none",
            background: "transparent",
          }}
        />
      </Sider>
      <Layout
        style={{
          marginLeft: collapsed ? 72 : 240,
          transition: "margin-left 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
        }}
      >
        <Header
          style={{
            padding: "0 24px",
            background: "rgba(255, 255, 255, 0.85)",
            backdropFilter: "blur(12px)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "sticky",
            top: 0,
            zIndex: 1,
            borderBottom: "1px solid #F0EDE8",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            {React.createElement(
              collapsed ? MenuUnfoldOutlined : MenuFoldOutlined,
              {
                className: "trigger",
                style: { fontSize: 18, cursor: "pointer" },
                onClick: () => setCollapsed(!collapsed),
              },
            )}
            <Typography.Title level={5} style={{ margin: 0 }}>
              {navItems.find((m) => m.key === location.pathname)?.label ||
                "概览"}
            </Typography.Title>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Button
              type="default"
              icon={<Bot size={16} />}
              onClick={() => setRightDrawerOpen(!rightDrawerOpen)}
            >
              AI助手
            </Button>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div
                style={{
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                }}
              >
                <Avatar style={{ backgroundColor: "#0EA5E9" }}>
                  {user.name?.charAt(0) || "U"}
                </Avatar>
                <DownOutlined style={{ fontSize: 12, color: "#999" }} />
              </div>
            </Dropdown>
          </div>
        </Header>
        <Layout
          ref={containerRef}
          style={{
            flexDirection: "row",
            height: "calc(100vh - 64px)",
            overflow: "hidden",
          }}
        >
          <Content
            style={{
              flex: 1,
              minWidth: 0,
              background: "transparent",
              overflow: "auto",
            }}
          >
            <Outlet />
          </Content>
          {rightDrawerOpen && (
            <>
              {/* Resizable AI Panel */}
              <div
                style={{
                  width: aiPanelWidth,
                  height: "calc(100vh - 64px)",
                  position: "relative",
                  background: "#fff",
                  borderLeft: "1px solid #F0EDE8",
                  overflow: "hidden",
                  transition: isDragging ? "none" : "width 0.2s ease",
                  minWidth: 0,
                  flexShrink: 0,
                }}
              >
                {/* Drag Handle */}
                <div
                  onMouseDown={handleDragStart}
                  onDoubleClick={handleMaxWidth}
                  style={{
                    position: "absolute",
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: 6,
                    cursor: "col-resize",
                    zIndex: 10,
                    background: isDragging ? "#0EA5E920" : "transparent",
                    transition: "background 0.2s",
                  }}
                />
                <AIAssistant />
              </div>
            </>
          )}
        </Layout>
      </Layout>
      {/* Mobile menu drawer for tablet */}
      <Drawer
        title="菜单"
        placement="left"
        onClose={() => setMobileMenuOpen(false)}
        open={mobileMenuOpen}
        width={240}
        styles={{ body: { padding: 0 } }}
      >
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={getMenuItems(false)}
          onClick={({ key }) => handleNav(key)}
        />
      </Drawer>
    </Layout>
  );
};

export default MainLayout;
