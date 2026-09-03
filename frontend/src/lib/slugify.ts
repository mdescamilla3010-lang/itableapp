export function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[^\x00-\x7F]/g, "") // strip accents/diacritics left over after NFD
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
