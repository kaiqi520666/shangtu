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
  const map = {
    recharge: "充值",
    consume: "消费",
    refund: "退款",
    admin_adjust: "后台调整",
  };
  return map[type] || type || "-";
}

export function totalPages(state) {
  return Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
}
