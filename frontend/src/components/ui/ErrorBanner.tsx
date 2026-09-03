import { ApiError } from "../../api/client";

export function ErrorBanner({ error }: { error: unknown }) {
  const message = error instanceof ApiError ? error.message : "Ocurrió un error inesperado.";
  return (
    <div className="banner banner--error" role="alert">
      <span>⚠</span>
      <span>{message}</span>
    </div>
  );
}
