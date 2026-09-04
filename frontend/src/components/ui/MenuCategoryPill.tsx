import type { MenuCategory } from "../../api/types";
import { MENU_CATEGORY_LABELS } from "../../lib/labels";

const VARIANT: Record<MenuCategory, string> = {
  ESTRELLA: "pill--success",
  CABALLO_DE_BATALLA: "pill--primary",
  PUZZLE: "pill--warning",
  PERRO: "pill--danger",
};

export function MenuCategoryPill({ category }: { category: MenuCategory }) {
  return (
    <span className={`pill ${VARIANT[category]}`}>
      <span className="pill__dot" />
      {MENU_CATEGORY_LABELS[category]}
    </span>
  );
}
