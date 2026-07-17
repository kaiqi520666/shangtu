import { useAuthStore } from "@/stores/auth.js";

export function handleUnauthorized(
  status,
  redirect = (url) => window.location.assign(url),
) {
  if (status !== 401) return;

  useAuthStore().logout();
  if (!["/login", "/register"].includes(window.location.pathname)) {
    const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
    redirect(`/login?redirect=${encodeURIComponent(currentPath)}`);
  }
}
