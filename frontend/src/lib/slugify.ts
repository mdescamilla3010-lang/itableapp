export function slugify(value: string): string {
  const asciiOnly = value
    .normalize("NFD")
    .split("")
    .filter((char) => char.charCodeAt(0) <= 127)
    .join("");

  return asciiOnly
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
