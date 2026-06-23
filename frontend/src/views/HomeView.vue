<script setup>
import { RouterLink } from "vue-router";
import { ArrowRight, Clapperboard, ImagePlus, Layers3, Shirt, Sparkles } from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth.js";

const authStore = useAuthStore();
const loginTarget = { path: "/login", query: { redirect: "/generator/product-suite" } };

const featureItems = [
  { icon: Layers3, title: "商品套图", desc: "批量生成主图、场景图、卖点图和细节图。" },
  { icon: ImagePlus, title: "商品详情图", desc: "根据卖点生成多张详情页模块图。" },
  { icon: Clapperboard, title: "商品视频", desc: "用商品图生成 UGC 种草、产品演示和广告短片。" },
  { icon: Shirt, title: "服饰穿搭", desc: "上传服装图，搭配模特和拍摄场景。" },
  { icon: Sparkles, title: "自由生图", desc: "支持文生图和参考图生图。" },
];
</script>

<template>
  <div class="min-h-screen bg-slate-50 text-slate-900">
    <header class="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
      <div class="flex items-center gap-3">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/10 bg-white shadow-sm"
        >
          <img src="/logo.png" class="h-8 w-8 object-contain" alt="商图 AI Logo" />
        </div>
        <div>
          <p class="text-sm font-bold text-slate-900">商图 AI</p>
          <p class="text-xs text-slate-500">AI 电商内容生成工作台</p>
        </div>
      </div>
    </header>

    <main
      class="mx-auto grid min-h-[calc(100vh-80px)] max-w-6xl content-center gap-10 px-6 py-10 lg:grid-cols-[1fr_420px] lg:items-center"
    >
      <section class="max-w-2xl">
        <p class="mb-4 text-xs font-bold uppercase tracking-[0.18em] text-primary">
          商图 AI 工作台
        </p>
        <h1 class="text-4xl font-black leading-tight text-slate-950 md:text-5xl">
          AI 电商内容生成工作台
        </h1>
        <p class="mt-5 max-w-xl text-sm leading-7 text-slate-600">
          上传商品图，批量生成商品套图、详情图、商品视频、服饰穿搭图和自由生图素材，让电商内容生产更快进入可用状态。
        </p>
        <div class="mt-8 flex flex-wrap items-center gap-3">
          <RouterLink
            v-if="authStore.isAuthenticated"
            to="/generator/product-suite"
            class="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-white shadow-md transition-colors hover:bg-secondary"
          >
            进入工作台
            <ArrowRight class="h-4 w-4" />
          </RouterLink>
          <template v-else>
            <RouterLink
              :to="loginTarget"
              class="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-white shadow-md transition-colors hover:bg-secondary"
            >
              登录
              <ArrowRight class="h-4 w-4" />
            </RouterLink>
            <RouterLink
              to="/register"
              class="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:border-primary/40 hover:text-primary"
            >
              注册
            </RouterLink>
          </template>
        </div>
      </section>

      <section class="grid gap-3">
        <div
          v-for="item in featureItems"
          :key="item.title"
          class="flex gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div
            class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"
          >
            <component :is="item.icon" class="h-5 w-5" />
          </div>
          <div>
            <h2 class="text-sm font-bold text-slate-900">{{ item.title }}</h2>
            <p class="mt-1 text-xs leading-5 text-slate-500">{{ item.desc }}</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
