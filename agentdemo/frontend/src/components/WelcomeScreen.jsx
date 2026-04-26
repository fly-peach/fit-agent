function WelcomeScreen({ onStart }) {
  return (
    <div className="welcome-page">
      <div className="welcome-content">
        <div className="header-frame">
          <div className="icon-frame">
            <svg className="sparkles-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
              <path d="M5 3v4" />
              <path d="M19 17v4" />
              <path d="M3 5h4" />
              <path d="M17 19h4" />
            </svg>
          </div>
          <div className="title-frame">
            <h1 className="main-title">AI 智能助手</h1>
            <p className="sub-title">您的智能对话伙伴</p>
          </div>
        </div>

        <div className="spacer" />

        <div className="features-frame">
          <div className="feature-card">
            <div className="feature-icon feature-icon-1">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
            </div>
            <h3 className="feature-title">实时流式输出</h3>
            <p className="feature-desc">采用流式输出技术，让您即时看到回复内容</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon feature-icon-2">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z" />
                <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z" />
              </svg>
            </div>
            <h3 className="feature-title">深度推理</h3>
            <p className="feature-desc">展示AI的完整思考过程，让推理过程清晰可见</p>
          </div>

          <div className="feature-card">
            <div className="feature-icon feature-icon-3">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
              </svg>
            </div>
            <h3 className="feature-title">工具集成</h3>
            <p className="feature-desc">支持代码执行、数学计算等外部能力调用</p>
          </div>
        </div>

        <div className="spacer" />

        <button className="start-btn" onClick={onStart}>
          <span>开始对话</span>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default WelcomeScreen;
