import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { login } from "../../shared/api/client";
import { useAuthStore } from "../../store/auth";

function useRedirectTarget() {
  const location = useLocation();
  const query = new URLSearchParams(location.search);
  return query.get("redirect") || "/dashboard";
}

export function LoginPage() {
  const navigate = useNavigate();
  const redirect = useRedirectTarget();
  const setSession = useAuthStore((s) => s.setSession);
  const [account, setAccount] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const tokens = await login({ account, password });
      setSession(tokens);
      navigate(redirect, { replace: true });
    } catch {
      setError("登录失败，请检查账号或密码");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>账号登录</h1>
        <label>账号（邮箱或手机号）</label>
        <input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="请输入账号" />
        <label>密码</label>
        <div className="password-field">
          <input
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="请输入密码"
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? "隐藏密码" : "显示密码"}
            title={showPassword ? "隐藏密码" : "显示密码"}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Zm10 3.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7Z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>
        {error && <p className="error-text">{error}</p>}
        <button className="primary-btn" type="submit" disabled={submitting}>
          {submitting ? "登录中..." : "登录"}
        </button>
        <p className="muted-text">
          还没有账号？<Link to="/register">去注册</Link>
        </p>
      </form>
    </div>
  );
}
