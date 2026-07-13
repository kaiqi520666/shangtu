<script setup>
import AdminCreditCostSection from "@/components/admin/settings/AdminCreditCostSection.vue";

defineProps({
  state: { type: Object, required: true },
});

const tierFields = [
  { key: "standard", label: "标准档" },
  { key: "premium", label: "高质档" },
];
</script>

<template>
  <AdminCreditCostSection title="生图扣费" description="按分辨率配置每张图消耗积分。">
    <div class="grid gap-3 md:grid-cols-3">
      <label v-for="resolution in ['1K', '2K', '4K']" :key="resolution" class="block">
        <span class="text-xs font-bold text-slate-600">{{ resolution }} 扣费</span>
        <input v-model.number="state.imageCreditCosts[resolution]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
    </div>
  </AdminCreditCostSection>

  <AdminCreditCostSection title="商品视频扣费" description="按清晰度配置每秒消耗积分，实际扣费 = 时长 × 每秒积分。">
    <div class="grid gap-3 md:grid-cols-2">
      <label v-for="resolution in ['720p', '1080p']" :key="resolution" class="block">
        <span class="text-xs font-bold text-slate-600">{{ resolution }} 每秒扣费</span>
        <input v-model.number="state.videoCreditCosts[resolution]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
    </div>
  </AdminCreditCostSection>

  <AdminCreditCostSection title="数字人每秒扣费" description="数字人独立收费体系，按档位配置每秒积分。">
    <div class="grid gap-3 md:grid-cols-2">
      <label v-for="field in tierFields" :key="field.key" class="block">
        <span class="text-xs font-bold text-slate-600">{{ field.label }}每秒扣费</span>
        <input v-model.number="state.digitalHumanCreditCosts[field.key]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
    </div>
  </AdminCreditCostSection>

  <AdminCreditCostSection title="数字人预扣费" description="按档位配置预扣积分，创建任务时先扣，失败自动退回。">
    <div class="grid gap-3 md:grid-cols-2">
      <label v-for="field in tierFields" :key="field.key" class="block">
        <span class="text-xs font-bold text-slate-600">{{ field.label }}预扣</span>
        <input v-model.number="state.digitalHumanPrechargeCosts[field.key]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
    </div>
  </AdminCreditCostSection>

  <AdminCreditCostSection title="视频翻译扣费" description="视频翻译独立收费体系，按档位配置每秒积分。">
    <div class="grid gap-3 md:grid-cols-2">
      <label v-for="field in tierFields" :key="field.key" class="block">
        <span class="text-xs font-bold text-slate-600">{{ field.label }}翻译每秒扣费</span>
        <input v-model.number="state.videoTranslationCreditCosts[field.key]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
    </div>
  </AdminCreditCostSection>

  <AdminCreditCostSection title="AI 配音扣费" description="按每100个非空白字符配置积分，不足100字符按100字符计。">
    <label class="block max-w-sm">
      <span class="text-xs font-bold text-slate-600">每100字符扣费</span>
      <input v-model.number="state.voiceoverCreditCostPer100Chars" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
    </label>
  </AdminCreditCostSection>
</template>
