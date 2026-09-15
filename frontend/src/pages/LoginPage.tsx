import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../api/auth";
import { EyeIcon, EyeOffIcon } from "../components/layout/icons";
import { Logomark } from "../components/layout/Logomark";
import { ErrorBanner } from "../components/ui/ErrorBanner";
import { useTenantContext } from "../context/useTenantContext";

type Tab = "login" | "signup";

export function LoginPage() {
  const navigate = useNavigate();
  const { selectTenant } = useTenantContext();
  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const loginMutation = useMutation({
    mutationFn: () => authApi.login(email.trim(), password),
    onSuccess: (result) => {
      selectTenant(result.tenant_id, result.access_token);
      navigate("/");
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!email.trim() || !password) return;
    loginMutation.mutate();
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-card__brand">
          <Logomark size={32} />
          <span className="login-card__brand-name">itable app</span>
        </div>

        <div>
          <h1 className="login-card__title">Bienvenido</h1>
          <p className="login-card__subtitle">Inicia sesión para ver el dashboard de tu negocio</p>
        </div>

        <div className="login-tabs">
          <button
            type="button"
            className={`login-tab${tab === "login" ? " active" : ""}`}
            onClick={() => setTab("login")}
          >
            Iniciar sesión
          </button>
          <button
            type="button"
            className={`login-tab${tab === "signup" ? " active" : ""}`}
            onClick={() => setTab("signup")}
          >
            Crear cuenta
          </button>
        </div>

        {tab === "signup" ? (
          <p className="text-muted" style={{ margin: 0 }}>
            Las cuentas las crea tu administrador. Pídele que te dé de alta con tu correo para poder
            iniciar sesión.
          </p>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <div className="field">
              <label htmlFor="login-email">Correo electrónico</label>
              <input
                id="login-email"
                type="email"
                className="input"
                placeholder="tu@correo.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
                required
              />
            </div>

            <div className="field">
              <label htmlFor="login-password">Contraseña</label>
              <div className="login-password-field">
                <input
                  id="login-password"
                  type={showPassword ? "text" : "password"}
                  className="input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  className="login-password-toggle"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>
            </div>

            {loginMutation.isError && <ErrorBanner error={loginMutation.error} />}

            <button
              type="submit"
              className="btn btn--primary"
              style={{ width: "100%", padding: "12px" }}
              disabled={loginMutation.isPending}
            >
              {loginMutation.isPending ? "Entrando…" : "Iniciar sesión"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
