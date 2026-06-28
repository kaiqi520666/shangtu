export function getApiErrorMessage(error, fallback) {
  if (error?.response?.status === 401) {
    return "登录已过期，请重新登录";
  }
  return error?.response?.data?.message || fallback;
}
