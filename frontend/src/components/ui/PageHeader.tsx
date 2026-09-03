import type { ReactNode } from "react";

interface PageHeaderProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: "16px" }}>
      <div>
        <h1>{title}</h1>
        {description && <p className="text-muted" style={{ marginTop: "4px" }}>{description}</p>}
      </div>
      {action}
    </div>
  );
}
