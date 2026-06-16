import request from "./request.js";

export function getAdminOverview() {
  return request.get("/admin/overview", { timeout: 15000 });
}

export function getAdminUsers(params = {}) {
  return request.get("/admin/users", { params, timeout: 15000 });
}

export function updateAdminUser(userId, payload) {
  return request.patch(`/admin/users/${userId}`, payload, { timeout: 15000 });
}

export function adjustAdminUserCredits(userId, payload) {
  return request.post(`/admin/users/${userId}/credits/adjust`, payload, { timeout: 15000 });
}

export function getAdminCreditOrders(params = {}) {
  return request.get("/admin/credit-orders", { params, timeout: 15000 });
}

export function getAdminCreditTransactions(params = {}) {
  return request.get("/admin/credit-transactions", { params, timeout: 15000 });
}
