export function Spinner() {
  return <span className="spinner" role="status" aria-label="Cargando" />;
}

export function LoadingRow({ label = "Cargando…" }: { label?: string }) {
  return (
    <div className="loading-row">
      <Spinner />
      <span>{label}</span>
    </div>
  );
}
