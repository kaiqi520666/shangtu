export const adminTabs = [
  { key: "overview", label: "概览", to: "/admin/overview" },
  { key: "users", label: "用户", to: "/admin/users" },
  { key: "orders", label: "订单", to: "/admin/orders" },
  { key: "transactions", label: "流水", to: "/admin/transactions" },
];

export const userRoleOptions = [
  { label: "全部角色", value: "" },
  { label: "普通用户", value: "user" },
  { label: "超级管理员", value: "super_admin" },
];

export const userStatusOptions = [
  { label: "全部状态", value: "" },
  { label: "正常", value: "active" },
  { label: "已禁用", value: "disabled" },
];

export const orderStatusOptions = [
  { label: "全部状态", value: "" },
  { label: "待支付", value: "pending" },
  { label: "已支付", value: "paid" },
  { label: "失败", value: "failed" },
];

export const transactionTypeOptions = [
  { label: "全部类型", value: "" },
  { label: "充值", value: "recharge" },
  { label: "消费", value: "consume" },
  { label: "退款", value: "refund" },
  { label: "后台调整", value: "admin_adjust" },
];

export function formatMoney(amountCents) {
  return `¥${(Number(amountCents || 0) / 100).toFixed(2)}`;
}

export function formatTime(value) {
  if (!value) return "-";
  try {
    return new Date(value).toLocaleString("zh-CN", { hour12: false });
  } catch {
    return value;
  }
}

export function roleLabel(role) {
  return role === "super_admin" ? "超级管理员" : "普通用户";
}

export function statusLabel(status) {
  return status === "disabled" ? "已禁用" : "正常";
}

export function transactionTypeLabel(type) {
  const match = transactionTypeOptions.find((option) => option.value === type);
  return match?.label || type || "-";
}

export function totalPages(state) {
  return Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
}
