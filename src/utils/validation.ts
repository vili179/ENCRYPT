const ALLOWED_EXTENSIONS = new Set(["png", "jpg", "jpeg", "heic", "heif"]);

export function isAllowedFile(filename: string): boolean {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex === -1) return false;
  return ALLOWED_EXTENSIONS.has(filename.slice(dotIndex + 1).toLowerCase());
}
