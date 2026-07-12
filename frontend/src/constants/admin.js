export const adminTabs = [
  { key: "overview", label: "概览", to: "/admin/overview" },
  { key: "users", label: "用户", to: "/admin/users" },
  { key: "orders", label: "订单", to: "/admin/orders" },
  { key: "transactions", label: "流水", to: "/admin/transactions" },
  { key: "commissionWithdrawals", label: "提现审核", to: "/admin/commission-withdrawals" },
  { key: "imageTasks", label: "生成任务", to: "/admin/image-tasks" },
  { key: "assets", label: "管理资产", to: "/admin/assets" },
  { key: "settings", label: "系统配置", to: "/admin/settings" },
  { key: "productCatalog", label: "商品目录", to: "/admin/product-catalog" },
  { key: "promptTemplates", label: "提示词", to: "/admin/prompt-templates" },
  { key: "outfitModels", label: "模特库", to: "/admin/outfit-models" },
  { key: "heygenAvatars", label: "系统数字人", to: "/admin/heygen-avatars" },
  { key: "heygenVoices", label: "系统声音", to: "/admin/heygen-voices" },
  { key: "heygenTranslationLanguages", label: "翻译语言", to: "/admin/heygen-translation-languages" },
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

export const taskMediaTypeOptions = [
  { label: "全部媒体", value: "" },
  { label: "图片", value: "image" },
  { label: "视频", value: "video" },
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
  { label: "更新用户业务设置", value: "update_user_business" },
  { label: "通过提现审核", value: "approve_commission_withdrawal" },
  { label: "驳回提现", value: "reject_commission_withdrawal" },
  { label: "确认佣金打款", value: "pay_commission_withdrawal" },
  { label: "更新配置", value: "update_settings" },
  { label: "更新商品目录", value: "update_product_catalog" },
  { label: "新增提示词", value: "create_prompt_template" },
  { label: "更新提示词", value: "update_prompt_template" },
  { label: "新增系统模特", value: "create_outfit_model" },
  { label: "更新系统模特", value: "update_outfit_model" },
  { label: "删除系统模特", value: "delete_outfit_model" },
  { label: "同步 HeyGen 资源", value: "sync_heygen_resources" },
  { label: "同步 HeyGen 翻译语言", value: "sync_heygen_translation_languages" },
  { label: "更新系统数字人", value: "update_heygen_avatar" },
  { label: "更新系统声音", value: "update_heygen_voice" },
  { label: "更新翻译语言", value: "update_heygen_translation_language" },
];

export const activeStatusOptions = [
  { label: "全部状态", value: "" },
  { label: "启用", value: "true" },
  { label: "停用", value: "false" },
];

export const heygenGenderOptions = [
  { label: "全部性别", value: "" },
  { label: "女", value: "female" },
  { label: "男", value: "male" },
  { label: "未知", value: "unknown" },
];

export const heygenAvatarOrientationOptions = [
  { label: "全部方向", value: "" },
  { label: "竖版", value: "portrait" },
  { label: "横版", value: "landscape" },
];

export const heygenAvatarEngineOptions = [
  { label: "全部引擎", value: "" },
  { label: "Avatar III", value: "avatar_iii" },
  { label: "Avatar IV", value: "avatar_iv" },
  { label: "Avatar V", value: "avatar_v" },
];

export const heygenVoiceLocaleOptions = [
  { label: "全部 Locale", value: "" },
  { label: "支持", value: "true" },
  { label: "不支持", value: "false" },
];

export const heygenVoicePauseOptions = [
  { label: "全部 Pause", value: "" },
  { label: "支持", value: "true" },
  { label: "不支持", value: "false" },
];

export const heygenVoiceLanguageOptions = [
  { label: "全部语言", value: "" },
  { label: "全球 / 多语种", value: "__multilingual__" },
  { label: "英语", value: "English" },
  { label: "中文", value: "Chinese" },
  { label: "日语", value: "Japanese" },
  { label: "韩语", value: "Korean" },
  { label: "西班牙语", value: "Spanish" },
  { label: "法语", value: "French" },
  { label: "德语", value: "German" },
  { label: "葡萄牙语", value: "Portuguese" },
  { label: "阿拉伯语", value: "Arabic" },
];

export const promptPurposeOptions = [
  { label: "全部用途", value: "" },
  { label: "生图", value: "image_generate" },
  { label: "AI帮写", value: "ai_write" },
  { label: "策略/提示词", value: "strategy" },
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

export function orderStatusLabel(status) {
  const match = orderStatusOptions.find((option) => option.value === status);
  return match?.label || status || "-";
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

export function productCatalogScenarioLabel(scenario) {
  const match = scenarioOptions.find((option) => option.value === scenario);
  return match?.label || scenario || "-";
}

export function promptPurposeLabel(purpose, scenario = "") {
  if (scenario === "product_video" && purpose === "strategy") return "视频提示词生成";
  const match = promptPurposeOptions.find((option) => option.value === purpose);
  return match?.label || purpose || "-";
}

export function promptTemplateScopeLabel(template = {}) {
  const typeId = template.type_id || "";
  if (template.scenario === "product_video") {
    return typeId ? `视频方向：${typeId}` : "全部视频方向";
  }
  if (template.scenario === "free_video") {
    return typeId ? `自由视频类型：${typeId}` : "全部自由视频类型";
  }
  if (template.scenario === "product_suite") {
    return typeId ? `套图类型：${typeId}` : "全部套图类型";
  }
  if (template.scenario === "product_image") {
    return typeId ? `详情图种：${typeId}` : "全部详情图种";
  }
  if (template.scenario === "outfit") {
    return typeId ? `穿搭场景：${typeId}` : "全部穿搭场景";
  }
  return typeId ? `type_id：${typeId}` : "全部类型";
}

export function activeStatusLabel(active) {
  return active ? "启用" : "停用";
}

export function auditActionLabel(action) {
  const match = auditActionOptions.find((option) => option.value === action);
  return match?.label || action || "-";
}

export function heygenAvatarEngineLabel(engine) {
  if (engine === "avatar_iv") return "Avatar IV";
  if (engine === "avatar_v") return "Avatar V";
  if (engine === "avatar_iii") return "Avatar III";
  return engine || "-";
}

export function totalPages(state) {
  return Math.max(1, Math.ceil(Number(state.total || 0) / Number(state.pageSize || 20)));
}
import { scenarioOptions } from "@/constants/scenarios.js";

export { scenarioOptions };
