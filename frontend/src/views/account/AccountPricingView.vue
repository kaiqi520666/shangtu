<script setup>
import { computed, onMounted } from "vue";
import { AudioLines, Image, Languages, UserRound, Video } from "lucide-vue-next";
import { useAccountPricing } from "@/composables/account/useAccountPricing.js";

const { adjusted, loading, loadPricing } = useAccountPricing();

const groups = computed(() => {
  if (!adjusted.value) return [];
  return [
    {
      key: "image",
      label: "图片生成",
      icon: Image,
      items: Object.entries(adjusted.value.image).map(([label, value]) => ({ label, value, unit: "积分/张" })),
    },
    {
      key: "video",
      label: "视频生成",
      icon: Video,
      items: Object.entries(adjusted.value.video).map(([label, value]) => ({ label, value, unit: "积分/秒" })),
    },
    {
      key: "digital-human",
      label: "数字人",
      icon: UserRound,
      items: [
        { label: "标准档", value: adjusted.value.digitalHuman.standard, unit: "积分/秒" },
        { label: "高质档", value: adjusted.value.digitalHuman.premium, unit: "积分/秒" },
        { label: "标准档预扣", value: adjusted.value.digitalHumanPrecharge.standard, unit: "积分" },
        { label: "高质档预扣", value: adjusted.value.digitalHumanPrecharge.premium, unit: "积分" },
      ],
    },
    {
      key: "translation",
      label: "视频翻译",
      icon: Languages,
      items: [
        { label: "标准档", value: adjusted.value.videoTranslation.standard, unit: "积分/秒" },
        { label: "高质档", value: adjusted.value.videoTranslation.premium, unit: "积分/秒" },
      ],
    },
    {
      key: "voiceover",
      label: "AI 配音",
      icon: AudioLines,
      items: [{ label: "文本配音", value: adjusted.value.voiceover, unit: "积分/100字符" }],
    },
  ];
});

function formatCost(value) {
  return Number.isInteger(Number(value)) ? Number(value) : Number(Number(value).toFixed(2));
}

onMounted(loadPricing);
</script>

<template>
  <section class="mx-auto max-w-6xl">
    <div class="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <header class="flex items-center justify-between gap-4 border-b border-slate-100 px-5 py-4">
        <div>
          <h2 class="text-sm font-black text-slate-900">计费标准</h2>
          <p class="mt-1 text-xs font-semibold text-slate-400">当前账号计费</p>
        </div>
        <span class="rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-2 text-xs font-black text-emerald-700">消费倍率 {{ Number(adjusted?.multiplier || 1).toFixed(2) }}×</span>
      </header>

      <div v-if="loading" class="px-5 py-16 text-center text-sm text-slate-400">正在加载计费标准...</div>
      <div v-else class="divide-y divide-slate-100">
        <section v-for="group in groups" :key="group.key" class="grid gap-4 px-5 py-5 md:grid-cols-[180px_1fr] md:items-start">
          <div class="flex items-center gap-2 text-sm font-black text-slate-800">
            <component :is="group.icon" class="h-4 w-4 text-slate-400" />
            {{ group.label }}
          </div>
          <div class="flex flex-wrap gap-2">
            <div v-for="item in group.items" :key="item.label" class="min-w-36 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2.5">
              <p class="text-[11px] font-bold text-slate-400">{{ item.label }}</p>
              <p class="mt-1 text-sm font-black text-slate-900">{{ formatCost(item.value) }} <span class="text-xs text-slate-500">{{ item.unit }}</span></p>
            </div>
          </div>
        </section>
      </div>
    </div>
  </section>
</template>
