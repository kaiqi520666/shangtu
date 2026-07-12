import request from "./request.js";

export function getBillingPackages() {
  return request.get("/billing/packages", { timeout: 15000 });
}

export function createBillingOrder(packageId) {
  return request.post("/billing/orders", { package_id: packageId }, { timeout: 30000 });
}

export function getBillingOrder(orderId) {
  return request.get(`/billing/orders/${orderId}`, { timeout: 15000 });
}

export function redeemCouponCode(code) {
  return request.post("/account/coupon-redemptions", { code }, { timeout: 15000 });
}
