// src/api/request.js
import axios from "axios";
import { useAuthStore } from "@/stores/auth.js";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 10000,
});

request.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  const token = authStore.token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => {
    const payload = response.data;
    const credits = payload?.data?.credits;
    if (credits !== undefined && credits !== null) {
      const authStore = useAuthStore();
      authStore.updateCredits(credits);
    }
    return payload;
  },
  handleResponseError,
);

export function handleResponseError(
  error,
  redirect = (url) => window.location.assign(url),
) {
  if (error.response?.status === 401) {
    useAuthStore().logout();
    if (!['/login', '/register'].includes(window.location.pathname)) {
      const currentPath = `${window.location.pathname}${window.location.search}${window.location.hash}`;
      redirect(`/login?redirect=${encodeURIComponent(currentPath)}`);
    }
  }
  return Promise.reject(error);
}

export default request;
