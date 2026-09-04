import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

function InboxIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} width={20} height={20}>
      <path d="M3.5 12.5h4.7a1 1 0 0 1 .95.68l.5 1.5a1 1 0 0 0 .95.68h2.8a1 1 0 0 0 .95-.68l.5-1.5a1 1 0 0 1 .95-.68h4.7" />
      <path d="M5.2 6 3.5 12.2v6a1.3 1.3 0 0 0 1.3 1.3h14.4a1.3 1.3 0 0 0 1.3-1.3v-6L18.8 6a1.3 1.3 0 0 0-1.25-.95H6.45A1.3 1.3 0 0 0 5.2 6Z" />
    </svg>
  );
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <span className="empty-state__icon">
        <InboxIcon />
      </span>
      <p className="empty-state__title">{title}</p>
      {description && <p>{description}</p>}
      {action}
    </div>
  );
}
