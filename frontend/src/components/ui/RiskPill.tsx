import type { RiskLevel } from "../../api/types";
import { RISK_LABELS } from "../../lib/labels";

const VARIANT: Record<RiskLevel, string> = {
  HIGH_RISK: "pill--danger",
  MEDIUM_RISK: "pill--warning",
  NORMAL: "pill--success",
};

export function RiskPill({ level }: { level: RiskLevel }) {
  return (
    <span className={`pill ${VARIANT[level]}`}>
      <span className="pill__dot" />
      {RISK_LABELS[level]}
    </span>
  );
}
