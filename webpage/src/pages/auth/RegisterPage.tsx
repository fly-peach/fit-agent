import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../../shared/api/client";
import { useAuthStore } from "../../store/auth";

export function RegisterPage() {
  const navigate = useNavigate();
  const setSession = useAuthStore((s) => s.setSession);
  const [account, setAccount] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (password.length < 8) {
      setError("密码长度至少为 8 位");
      return;
    }
    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const payload = account.includes("@") ? { email: account } : { phone: account };
      const result = await register({ ...payload, password });
      setSession(result);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : "注册失败，请稍后重试";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <form className="card auth-card" onSubmit={onSubmit}>
        <h1>创建账号</h1>
        <label>邮箱或手机号</label>
        <input value={account} onChange={(e) => setAccount(e.target.value)} placeholder="请输入邮箱或手机号" />
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
        <label>确认密码</label>
        <div className="password-field">
          <input
            type={showConfirmPassword ? "text" : "password"}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="请再次输入密码"
          />
          <button
            type="button"
            className="password-toggle"
            onClick={() => setShowConfirmPassword((v) => !v)}
            aria-label={showConfirmPassword ? "隐藏确认密码" : "显示确认密码"}
            title={showConfirmPassword ? "隐藏确认密码" : "显示确认密码"}
          >
            <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
              <path
                d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Zm10 3.5A3.5 3.5 0 1 0 12 8.5a3.5 3.5 0 0 0 0 7Z"
                fill="currentColor"
              />
            </svg>
          </button>
        </div>
        <p className="muted-text">注册成功后系统会自动生成学员 ID</p>
        {error && <p className="error-text">{error}</p>}
        <button className="primary-btn" type="submit" disabled={submitting}>
          {submitting ? "注册中..." : "注册并登录"}
        </button>
        <p className="muted-text">
          已有账号？<Link to="/login">去登录</Link>
        </p>
      </form>
    </div>
  );
}
