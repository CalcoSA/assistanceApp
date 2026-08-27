const getConfiguredApiUrl = () =>
  String(import.meta.env.VITE_API_URL || "")
    .trim()
    .replace(/\/+$/, "");

export const getBackendFileUrl = (path?: string | null) => {
  if (!path) return "";

  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const configuredApiUrl = getConfiguredApiUrl();

  if (normalizedPath.startsWith("/api/")) {
    return `${configuredApiUrl.replace(/\/api$/i, "")}${normalizedPath}`;
  }

  return `${configuredApiUrl}${normalizedPath}`;
};
