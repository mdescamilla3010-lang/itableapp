export function Logomark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" aria-hidden="true">
      <rect width="48" height="48" rx="11" fill="var(--color-primary)" />
      <rect x="10" y="10" width="12" height="12" rx="2.5" fill="#FBEAE1" />
      <rect x="26" y="10" width="12" height="12" rx="2.5" fill="#FBEAE1" fillOpacity="0.55" />
      <rect x="10" y="26" width="12" height="12" rx="2.5" fill="#FBEAE1" fillOpacity="0.55" />
      <rect x="26" y="26" width="12" height="12" rx="2.5" fill="#FBEAE1" />
    </svg>
  );
}
