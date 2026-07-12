import request from "./request.js";

export function getAccountProfile() {
  return request.get("/account/profile", { timeout: 15000 });
}

export function getAccountCreditTransactions(params = {}) {
  return request.get("/account/credit-transactions", { params, timeout: 15000 });
}

export function getDistributionOverview() {
  return request.get("/account/distribution/overview", { timeout: 15000 });
}

export function getDistributionDownlines(params = {}) {
  return request.get("/account/distribution/downlines", { params, timeout: 15000 });
}

export function updateDistributionDownlineRate(userId, commissionRate) {
  return request.patch(`/account/distribution/downlines/${userId}/rate`, { commission_rate: commissionRate }, { timeout: 15000 });
}

export function getCommissionTransactions(params = {}) {
  return request.get("/account/distribution/transactions", { params, timeout: 15000 });
}

export function getCommissionWithdrawals(params = {}) {
  return request.get("/account/distribution/withdrawals", { params, timeout: 15000 });
}

export function createCommissionWithdrawal(payload) {
  return request.post("/account/distribution/withdrawals", payload, { timeout: 15000 });
}
