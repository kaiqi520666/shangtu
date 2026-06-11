// src/api/request.js
import axios from "axios";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 10000,
});

request.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    return Promise.reject(error);
  },
);

export default request;

function getAuthToken() {
  try {
    const raw = window.localStorage.getItem("nodepass_auth_user");
    return raw ? JSON.parse(raw)?.token : "";
  } catch {
    return "";
  }
}
