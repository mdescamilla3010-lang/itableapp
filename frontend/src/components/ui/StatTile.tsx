interface StatTileProps {
  label: string;
  value: string;
  hint?: string;
  danger?: boolean;
}

export function StatTile({ label, value, hint, danger }: StatTileProps) {
  return (
    <div className="stat-tile">
      <span className="stat-tile__label">{label}</span>
      <span className={`stat-tile__value${danger ? " stat-tile__value--danger" : ""}`}>
        {value}
      </span>
      {hint && <span className="stat-tile__hint">{hint}</span>}
    </div>
  );
}
