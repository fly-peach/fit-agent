import React from 'react'
import { useNavigate } from 'react-router-dom'
import './index.css'

const LandingPage: React.FC = () => {
  const navigate = useNavigate()

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="landing-page">
      {/* Navigation */}
      <nav className="landing-nav">
        <div className="landing-nav-logo" onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}>FitAgent</div>
        <div className="landing-nav-links">
          <span className="landing-nav-link" onClick={() => scrollTo('features')}>功能</span>
          <span className="landing-nav-link" onClick={() => scrollTo('how-it-works')}>方案</span>
          <span className="landing-nav-link" onClick={() => scrollTo('cta')}>关于</span>
        </div>
        <button className="landing-nav-btn" type="button" onClick={() => navigate('/login')}>开始使用</button>
      </nav>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-badge">AI 驱动的健身智能体</div>
        <h1 className="landing-hero-title">你的健身，由 AI 守护</h1>
        <p className="landing-hero-desc">FitAgent 基于 AI 智能体技术，为你提供个性化的健身方案、实时运动指导、饮食管理和身体数据追踪，让每一次训练都更高效、更安全。</p>
        <div className="landing-hero-btns">
          <button className="landing-btn-primary" type="button" onClick={() => navigate('/login')}>立即体验</button>
          <button className="landing-btn-secondary" type="button" onClick={() => scrollTo('features')}>了解更多</button>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="landing-features">
        <div className="landing-section-header">
          <h2 className="landing-section-title">核心功能</h2>
          <p className="landing-section-desc">FitAgent 提供全方位的健身服务，帮助你科学训练、高效达成目标</p>
        </div>
        <div className="landing-features-grid">
          <FeatureCard icon="💪" title="智能训练计划" desc="AI 根据你的体能状况、目标和时间，自动生成个性化训练方案" />
          <FeatureCard icon="🥗" title="饮食管理" desc="记录每日饮食，AI 分析营养摄入，推荐健康食谱" />
          <FeatureCard icon="📈" title="数据追踪" desc="体重、体脂、BMI 等健康数据可视化，追踪你的进步" />
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="landing-how-it-works">
        <div className="landing-section-header">
          <h2 className="landing-section-title">如何使用</h2>
          <p className="landing-section-desc">简单的三步，开启你的智能健身之旅</p>
        </div>
        <div className="landing-steps">
          <Step num={1} title="注册账号" desc="快速注册，设置你的健身目标和基本体能信息" />
          <Step num={2} title="获取方案" desc="AI 分析你的数据，生成专属训练和饮食方案" />
          <Step num={3} title="开始训练" desc="按计划训练，记录数据，持续优化你的方案" />
        </div>
      </section>

      {/* CTA Section */}
      <section id="cta" className="landing-cta">
        <h2 className="landing-cta-title">准备好开始你的健身之旅了吗？</h2>
        <p className="landing-cta-desc">加入超过 10,000 名用户，体验 AI 驱动的科学健身</p>
        <button className="landing-btn-primary" type="button" onClick={() => navigate('/login')}>立即免费开始</button>
      </section>

      {/* Contact Section */}
      <section id="contact" className="landing-contact">
        <h2 className="landing-section-title">联系我们</h2>
        <div className="landing-contact-info">
          <p className="landing-contact-name">阿通</p>
          <p className="landing-contact-item">电话：15385335663</p>
          <p className="landing-contact-item">邮箱：1972127718@qq.com</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-footer-logo">FitAgent</div>
        <div className="landing-footer-links">
          <span className="landing-footer-link">隐私政策</span>
          <span className="landing-footer-link">服务条款</span>
          <span className="landing-footer-link" onClick={() => scrollTo('contact')}>联系我们</span>
        </div>
        <p className="landing-footer-copyright">&copy; 2026 FitAgent. All rights reserved.</p>
      </footer>
    </div>
  )
}

const FeatureCard: React.FC<{ icon: string; title: string; desc: string }> = ({ icon, title, desc }) => (
  <div className="landing-feature-card">
    <div className="landing-feature-icon">{icon}</div>
    <h3 className="landing-feature-title">{title}</h3>
    <p className="landing-feature-desc">{desc}</p>
  </div>
)

const Step: React.FC<{ num: number; title: string; desc: string }> = ({ num, title, desc }) => (
  <div className="landing-step">
    <div className="landing-step-num">{num}</div>
    <h3 className="landing-step-title">{title}</h3>
    <p className="landing-step-desc">{desc}</p>
  </div>
)

export default LandingPage
