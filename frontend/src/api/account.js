import request from "./request.js";

export function getAccountProfile() {
  return request.get("/account/profile", { timeout: 15000 });
}

export function getAccountCreditTransactions(params = {}) {
  return request.get("/account/credit-transactions", { params, timeout: 15000 });
}
