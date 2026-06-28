import { getImageCreditCosts } from "@/api/image.js";
import {
  defaultImageCreditCosts,
  getImageBatchCreditCost,
  getImageCreditCost,
  normalizeImageQuality,
} from "@/constants/generator.js";
import { useAuthStore } from "@/stores/auth.js";

let pendingCreditCosts = null;

function normalizeCosts(rawCosts) {
  if (!rawCosts || typeof rawCosts !== "object") return null;
  return Object.fromEntries(
    Object.entries(defaultImageCreditCosts).map(([quality, fallback]) => {
      const cost = Number(rawCosts[quality]);
      return [quality, Number.isFinite(cost) && cost > 0 ? cost : fallback];
    }),
  );
}

function createBusinessError(message) {
  const error = new Error(message || "计费配置异常");
  error.isBusinessError = true;
  return error;
}

export async function loadImageCreditCosts() {
  if (pendingCreditCosts) return pendingCreditCosts;

  pendingCreditCosts = getImageCreditCosts()
    .then((result) => {
      if (result.code !== 0) {
        throw createBusinessError(result.message || "计费配置异常");
      }
      return normalizeCosts(result.data?.costs) || defaultImageCreditCosts;
    })
    .catch((error) => {
      if (error?.isBusinessError) throw error;
      return defaultImageCreditCosts;
    })
    .finally(() => {
      pendingCreditCosts = null;
    });

  return pendingCreditCosts;
}

export async function ensureEnoughImageCredits({
  quality,
  count = 1,
  toast,
  actionText = "生成",
} = {}) {
  let costs = defaultImageCreditCosts;
  try {
    costs = await loadImageCreditCosts();
  } catch (error) {
    toast?.error(error.message || "计费配置异常，请检查后端 .env");
    return false;
  }
  const normalizedQuality = normalizeImageQuality(quality || "1K");
  const unitCost = getImageCreditCost(normalizedQuality, costs);
  const requiredCredits = getImageBatchCreditCost({
    quality: normalizedQuality,
    count,
    costs,
  });

  if (!unitCost || requiredCredits === null) {
    toast?.error("当前清晰度计费配置异常，请检查后端 .env");
    return false;
  }

  const authStore = useAuthStore();
  const availableCredits = Number(authStore.credits || 0);
  if (availableCredits >= requiredCredits) return true;

  toast?.info(
    `余额不足，${actionText}需要 ${requiredCredits} 点（${normalizedQuality} ${unitCost} 点/张 × ${count} 张），当前剩余 ${availableCredits} 点`,
  );
  return false;
}
