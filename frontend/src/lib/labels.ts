import type { MenuCategory, RiskLevel } from "../api/types";

export const RISK_LABELS: Record<RiskLevel, string> = {
  HIGH_RISK: "Alto riesgo",
  MEDIUM_RISK: "Riesgo medio",
  NORMAL: "Normal",
};

export const MENU_CATEGORY_LABELS: Record<MenuCategory, string> = {
  ESTRELLA: "Estrella",
  CABALLO_DE_BATALLA: "Caballo de batalla",
  PUZZLE: "Puzzle",
  PERRO: "Perro",
};

export const MENU_CATEGORY_DESCRIPTIONS: Record<MenuCategory, string> = {
  ESTRELLA: "Alto margen, alta popularidad",
  CABALLO_DE_BATALLA: "Bajo margen, alta popularidad",
  PUZZLE: "Alto margen, baja popularidad",
  PERRO: "Bajo margen, baja popularidad",
};
