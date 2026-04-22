import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuthStore } from "../store/auth";
import { AICoachSidebar } from "../features/ai-coach/AISidebar";

const navItems = [
  { to: "/data-overview", label: "数据总览" },
  { to: "/daily-metrics", label: "每日数据" },
  { to: "/daily-energy-workout", label: "饮食&训练" },
];

export function AppShell() {
  const clearSession = useAuthStore((s) => s.clearSession);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [agentOpen, setAgentOpen] = useState(true);
  const [agentWidth, setAgentWidth] = useState(425);

  const handleResizeAgent = (next: number) => {
    const clamped = Math.max(425, Math.min(680, next));
    setAgentWidth(clamped);
  };

  const coverRatio = Math.max(0, Math.min(1, (agentWidth - 425) / (680 - 425)));
  const coverOpacity = agentOpen ? 0.1 + coverRatio * 0.2 : 0;

  return (
    <div
      className={`app-shell ${leftCollapsed ? "left-collapsed" : ""} ${agentOpen ? "" : "agent-collapsed"}`}
      style={{
        ["--ai-width" as string]: `${agentWidth}px`,
        ["--ai-cover-opacity" as string]: `${coverOpacity}`,
      }}
    >
      <aside className={`sidebar ${leftCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-title">Rogers</div>
        <button className="left-collapse-btn" onClick={() => setLeftCollapsed((v) => !v)} type="button">
          {leftCollapsed ? ">" : "<"}
        </button>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-item active" : "nav-item")}
              title={item.label}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button className="logout-btn" onClick={clearSession}>
          退出登录
        </button>
      </aside>
      <main className="main-panel">
        <div className="main-panel-scroll">
          <Outlet />
        </div>
      </main>
      <AICoachSidebar
        open={agentOpen}
        onOpenChange={setAgentOpen}
        width={agentWidth}
        onResizeWidth={handleResizeAgent}
      />
    </div>
  );
}
