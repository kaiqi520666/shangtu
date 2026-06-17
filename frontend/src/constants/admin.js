export const adminTabs = [
  { key: "overview", label: "概览", to: "/admin/overview" },
  { key: "users", label: "用户", to: "/admin/users" },
  { key: "orders", label: "订单", to: "/admin/orders" },
  { key: "transactions", label: "流水", to: "/admin/transactions" },
  { key: "imageTasks", label: "生图任务", to: "/admin/image-tasks" },
  { key: "settings", label: "系统配置", to: "/admin/settings" },
  { key: "promptTemplates", label: "提示词", to: "/admin/prompt-templates" },
  { key: "outfitModels", label: "模特库", to: "/admin/outfit-models" },
  { key: "auditLogs", label: "审计日志", to: "/admin/audit-logs" },
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

export const imageTaskStatusOptions = [
  { label: "全部状态", value: "" },
  { label: "待处理", value: "pending" },
  { label: "生成中", value: "processing" },
  { label: "已完成", value: "done" },
  { label: "失败", value: "failed" },
  { label: "超时", value: "timeout" },
];

export const scenarioOptions = [
  { label: "全部场景", value: "" },
  { label: "商品套图", value: "product_suite" },
  { label: "商品详情图", value: "product_image" },
  { label: "服饰穿搭", value: "outfit" },
  { label: "自由生图", value: "free_image" },
];

export const promptScenarioOptions = [
  { label: "全部场景", value: "" },
  { label: "通用", value: "__global__" },
  ...scenarioOptions.filter((option) => option.value),
];

export const promptEditorScenarioOptions = [
  { label: "通用", value: "" },
  ...scenarioOptions.filter((option) => option.value),
];

export const auditActionOptions = [
  { label: "全部操作", value: "" },
  { label: "更新用户", value: "update_user" },
  { label: "调整积分", value: "adjust_credits" },
  { label: "更新配置", value: "update_settings" },
  { label: "新增提示词", value: "create_prompt_template" },
  { label: "更新提示词", value: "update_prompt_template" },
  { label: "新增系统模特", value: "create_outfit_model" },
  { label: "更新系统模特", value: "update_outfit_model" },
  { label: "停用系统模特", value: "delete_outfit_model" },
];

export const activeStatusOptions = [
  { label: "全部状态", value: "" },
  { label: "启用", value: "true" },
  { label: "停用", value: "false" },
];

export const promptPurposeOptions = [
  { label: "全部用途", value: "" },
  { label: "生图", value: "image_generate" },
  { label: "AI帮写", value: "ai_write" },
  { label: "详情策略", value: "strategy" },
];

export const promptModelOptions = [
  { label: "全部模型", value: "" },
  { label: "gpt-image-2", value: "gpt-image-2" },
  { label: "qwen3.6-flash", value: "qwen3.6-flash" },
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

export function imageTaskStatusLabel(status) {
  const match = imageTaskStatusOptions.find((option) => option.value === status);
  return match?.label || status || "-";
}

export function scenarioLabel(scenario) {
  if (!scenario) return "通用";
  const match = scenarioOptions.find((option) => option.value === scenario);
  return match?.label || scenario || "-";
}

export function promptPurposeLabel(purpose) {
  const match = promptPurposeOptions.find((option) => option.value === purpose);
  return match?.label || purpose || "-";
}

export function activeStatusLabel(active) {
  return active ? "启用" : "停用";
}

export function auditActionLabel(action) {
  const match = auditActionOptions.find((option) => option.value === action);
  return match?.label || action || "-";
}

export function totalPages(state) {
  return Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
}
