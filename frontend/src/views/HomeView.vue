<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { RouterLink } from "vue-router";
import {
  ArrowRight,
  Boxes,
  CheckCircle2,
  Clapperboard,
  FolderOpen,
  ImagePlus,
  Languages,
  Layers3,
  PlayCircle,
  Shirt,
  Sparkles,
  UserRound,
  WandSparkles,
  Workflow,
} from "lucide-vue-next";
import { useAuthStore } from "@/stores/auth.js";

const authStore = useAuthStore();

const images = {
  hero: "https://image.nodepass.net/generated/2/2026/07/d9566b18c3db4989a598f0db4fafd486.png",
  suite: "https://image.nodepass.net/generated/2/2026/07/de76ef7431fb435c8f29935f909f069f.png",
  detail: "https://image.nodepass.net/generated/2/2026/07/3458163d2a1e4adfb2c32b4038094648.png",
  outfit: "https://image.nodepass.net/generated/2/2026/07/b5b475e305c948388ef5777194d70d0f.png",
  video: "https://image.nodepass.net/generated/2/2026/07/22041c896cf54dbaa296296789e58100.png",
  avatar: "https://image.nodepass.net/generated/2/2026/07/9ce4c6aaa4d4478f9d9d68f60ecb1e7b.png",
};

const workspaceTarget = computed(() =>
  authStore.isAuthenticated
    ? "/generator/product-suite"
    : { path: "/login", query: { redirect: "/generator/product-suite" } },
);

onMounted(() => {
  document.documentElement.classList.add("scroll-smooth");
});

onBeforeUnmount(() => {
  document.documentElement.classList.remove("scroll-smooth");
});

const featureItems = [
  {
    icon: Layers3,
    title: "商品套图",
    desc: "批量生成主图、场景图、卖点图和细节图。",
    to: "/generator/product-suite",
    image: images.suite,
  },
  {
    icon: ImagePlus,
    title: "商品详情图",
    desc: "根据卖点生成详情页模块图。",
    to: "/generator/product-image",
    image: images.detail,
  },
  {
    icon: Clapperboard,
    title: "商品视频",
    desc: "生成 UGC 种草、产品演示和广告短片。",
    to: "/generator/product-video",
    image: images.video,
  },
  {
    icon: Shirt,
    title: "服饰穿搭",
    desc: "上传服装图，搭配模特和拍摄场景。",
    to: "/generator/outfit",
    image: images.outfit,
  },
  {
    icon: Sparkles,
    title: "自由生图",
    desc: "支持文生图和多参考图生图。",
    to: "/generator/free-image",
    image: images.detail,
  },
  {
    icon: PlayCircle,
    title: "自由生视频",
    desc: "用提示词、参考图、视频和音频生成短片。",
    to: "/generator/free-video",
    image: images.video,
  },
  {
    icon: UserRound,
    title: "数字人",
    desc: "创建数字人口播和产品讲解视频。",
    to: "/generator/digital-human",
    image: images.avatar,
  },
  {
    icon: Languages,
    title: "视频翻译",
    desc: "将视频翻译为多语言版本。",
    to: "/generator/video-translation",
    image: images.avatar,
  },
  {
    icon: FolderOpen,
    title: "资产库",
    desc: "统一管理上传素材和生成结果。",
    to: "/generator/assets",
    image: images.suite,
  },
];

const workflowItems = [
  { icon: ImagePlus, title: "上传素材", desc: "图片、视频、音频统一进入素材池。" },
  { icon: Workflow, title: "选择场景", desc: "套图、详情、视频、数字人流程直达。" },
  { icon: WandSparkles, title: "AI 生成", desc: "策略、提示词和参考素材协同生成。" },
  { icon: Boxes, title: "沉淀资产", desc: "结果自动进入资产库，方便复用下载。" },
];

const showcaseItems = [
  { title: "图片内容", desc: "商品套图、详情图、自由生图", image: images.suite },
  { title: "服饰内容", desc: "模特穿搭、场景拍摄、比例适配", image: images.outfit },
  { title: "视频内容", desc: "商品视频、自由生视频、短片封面", image: images.video },
  { title: "数字人与翻译", desc: "口播视频、多语言翻译、素材复用", image: images.avatar },
];
</script>

<template>
  <div class="min-h-screen scroll-smooth bg-slate-50 text-slate-950">
    <header class="sticky top-0 z-30 border-b border-slate-200 bg-white/85 backdrop-blur">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <RouterLink to="/" class="flex items-center gap-3">
          <span class="flex h-10 w-10 items-center justify-center rounded-xl border border-primary/15 bg-white shadow-sm">
            <img src="/logo.png" class="h-8 w-8 object-contain" alt="NodePass AI Logo" />
          </span>
          <span>
            <span class="block text-sm font-black text-slate-950">NodePass AI</span>
            <span class="block text-xs font-medium text-slate-500">电商内容生成平台</span>
          </span>
        </RouterLink>

        <nav class="hidden items-center rounded-full border border-slate-200 bg-slate-50 p-1 text-xs font-black text-slate-500 shadow-inner md:flex">
          <a href="#features" class="rounded-full px-4 py-2 transition-colors hover:bg-white hover:text-primary hover:shadow-sm">能力矩阵</a>
          <a href="#workflow" class="rounded-full px-4 py-2 transition-colors hover:bg-white hover:text-primary hover:shadow-sm">生成流程</a>
          <a href="#showcase" class="rounded-full px-4 py-2 transition-colors hover:bg-white hover:text-primary hover:shadow-sm">作品展示</a>
        </nav>

        <div class="flex items-center gap-2">
          <RouterLink
            v-if="authStore.isAuthenticated"
            to="/generator/product-suite"
            class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow-sm transition-colors hover:bg-secondary"
          >
            进入工作台
          </RouterLink>
          <template v-else>
            <RouterLink
              to="/login"
              class="hidden rounded-xl px-4 py-2 text-xs font-bold text-slate-600 transition-colors hover:text-primary sm:inline-flex"
            >
              登录
            </RouterLink>
            <RouterLink
              to="/register"
              class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow-sm transition-colors hover:bg-secondary"
            >
              注册
            </RouterLink>
          </template>
        </div>
      </div>
    </header>

    <main>
      <section class="relative overflow-hidden bg-slate-950">
        <img
          :src="images.hero"
          class="absolute inset-0 h-full w-full object-cover opacity-70"
          alt="NodePass AI 电商内容生成主视觉"
        />
        <div class="absolute inset-0 bg-slate-950/55"></div>

        <div class="relative mx-auto flex min-h-[78vh] max-w-7xl items-center px-5 py-20 lg:px-8">
          <section class="max-w-3xl text-white">
            <p class="mb-5 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold backdrop-blur">
              <WandSparkles class="h-4 w-4 text-primary" />
              AI 电商内容生成平台
            </p>
            <h1 class="text-4xl font-black leading-tight md:text-6xl">
              电商内容，一站生成
            </h1>
            <p class="mt-5 max-w-2xl text-base leading-8 text-slate-100 md:text-lg">
              商品图、详情页、短视频、数字人和视频翻译，统一在一个工作台完成。
            </p>
            <div class="mt-8 flex flex-wrap items-center gap-3">
              <RouterLink
                :to="workspaceTarget"
                class="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg transition-colors hover:bg-secondary"
              >
                开始创作
                <ArrowRight class="h-4 w-4" />
              </RouterLink>
              <RouterLink
                to="/generator/assets"
                class="inline-flex items-center gap-2 rounded-xl border border-white/25 bg-white/10 px-5 py-3 text-sm font-bold text-white backdrop-blur transition-colors hover:bg-white/20"
              >
                查看资产库
              </RouterLink>
            </div>
            <div class="mt-8 grid max-w-2xl gap-3 sm:grid-cols-3">
              <div class="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <CheckCircle2 class="mb-3 h-5 w-5 text-primary" />
                <p class="text-lg font-black text-white">图文视频</p>
                <p class="mt-1 text-xs leading-5 text-slate-200">覆盖商品图、短视频与详情内容</p>
              </div>
              <div class="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <CheckCircle2 class="mb-3 h-5 w-5 text-primary" />
                <p class="text-lg font-black text-white">资产复用</p>
                <p class="mt-1 text-xs leading-5 text-slate-200">上传素材与生成结果统一沉淀</p>
              </div>
              <div class="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <CheckCircle2 class="mb-3 h-5 w-5 text-primary" />
                <p class="text-lg font-black text-white">多语言扩展</p>
                <p class="mt-1 text-xs leading-5 text-slate-200">支持跨境内容翻译和本地化</p>
              </div>
            </div>
          </section>
        </div>
      </section>

      <section id="features" class="mx-auto max-w-7xl scroll-mt-24 px-5 py-16 lg:px-8">
        <div class="mb-8 max-w-3xl">
          <div>
            <p class="text-xs font-black uppercase text-primary">Creative Workspace</p>
            <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">覆盖电商内容生产全链路</h2>
          </div>
          <p class="mt-4 text-sm leading-7 text-slate-500">
            从素材上传到成品下载，功能入口集中在一个工作台，适合跨境电商、国内电商和短视频带货团队。
          </p>
        </div>

        <div class="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <RouterLink
            :to="featureItems[0].to"
            class="group relative min-h-[460px] overflow-hidden rounded-3xl bg-slate-950 p-6 text-white shadow-xl"
          >
            <img :src="featureItems[0].image" class="absolute inset-0 h-full w-full object-cover opacity-60 transition-transform duration-700 group-hover:scale-[1.04]" :alt="featureItems[0].title" />
            <div class="absolute inset-0 bg-slate-950/45"></div>
            <div class="relative flex h-full flex-col justify-between">
              <div class="flex items-center justify-between">
                <span class="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-black backdrop-blur">
                  核心能力
                </span>
                <span class="flex h-10 w-10 items-center justify-center rounded-full bg-white/15 backdrop-blur transition-colors group-hover:bg-primary">
                  <ArrowRight class="h-5 w-5" />
                </span>
              </div>
              <div>
                <component :is="featureItems[0].icon" class="mb-5 h-10 w-10 text-primary" />
                <h3 class="text-3xl font-black">{{ featureItems[0].title }}</h3>
                <p class="mt-3 max-w-md text-sm leading-7 text-slate-100">{{ featureItems[0].desc }}</p>
                <div class="mt-6 flex flex-wrap gap-2 text-xs font-bold text-white/85">
                  <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">主图</span>
                  <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">场景图</span>
                  <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">卖点图</span>
                  <span class="rounded-full bg-white/10 px-3 py-1 backdrop-blur">细节图</span>
                </div>
              </div>
            </div>
          </RouterLink>

          <div class="grid gap-4 sm:grid-cols-2">
            <RouterLink
              v-for="item in featureItems.slice(1)"
              :key="item.title"
              :to="item.to"
              class="group rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-1 hover:border-primary/35 hover:shadow-md"
            >
              <div class="flex items-start justify-between gap-4">
                <span class="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <component :is="item.icon" class="h-6 w-6" />
                </span>
                <ArrowRight class="h-4 w-4 text-slate-300 transition-colors group-hover:text-primary" />
              </div>
              <h3 class="mt-6 text-base font-black text-slate-950">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.desc }}</p>
            </RouterLink>
          </div>
        </div>
      </section>

      <section id="workflow" class="scroll-mt-24 border-y border-slate-200 bg-white">
        <div class="mx-auto max-w-7xl px-5 py-16 lg:px-8">
          <div class="mx-auto max-w-3xl text-center">
            <p class="text-xs font-black uppercase text-primary">Workflow</p>
            <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">从素材到成品，一条线完成</h2>
            <p class="mt-4 text-sm leading-7 text-slate-500">
              把上传、选择、生成和资产沉淀串成固定流程，减少重复配置，让团队更快拿到可用内容。
            </p>
          </div>

          <div class="relative mt-10 grid gap-4 lg:grid-cols-4">
            <div class="absolute left-10 right-10 top-12 hidden h-px bg-gradient-to-r from-primary/0 via-primary/40 to-primary/0 lg:block"></div>
            <article
              v-for="(item, index) in workflowItems"
              :key="item.title"
              class="relative rounded-3xl border border-slate-200 bg-slate-50 p-5 shadow-sm"
            >
              <div class="mb-6 flex items-center justify-between">
                <span class="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white shadow-lg shadow-primary/20">
                  <component :is="item.icon" class="h-6 w-6" />
                </span>
                <span class="font-mono text-3xl font-black text-slate-200">0{{ index + 1 }}</span>
              </div>
              <h3 class="text-base font-black text-slate-950">{{ item.title }}</h3>
              <p class="mt-2 text-sm leading-6 text-slate-500">{{ item.desc }}</p>
            </article>
          </div>
        </div>
      </section>

      <section id="showcase" class="mx-auto max-w-7xl scroll-mt-24 px-5 py-16 lg:px-8">
        <div class="mb-8">
          <p class="text-xs font-black uppercase text-primary">Showcase</p>
          <h2 class="mt-2 text-2xl font-black text-slate-950 md:text-3xl">面向真实电商场景的视觉输出</h2>
        </div>
        <div class="grid gap-5 lg:grid-cols-[1.15fr_0.85fr]">
          <article class="group overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <div class="relative">
              <img :src="showcaseItems[0].image" class="aspect-[16/10] w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" :alt="showcaseItems[0].title" />
              <div class="absolute left-4 top-4 rounded-full bg-white/90 px-3 py-1 text-xs font-black text-primary shadow-sm backdrop-blur">
                图片生产
              </div>
            </div>
            <div class="flex flex-col gap-4 p-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <h3 class="text-xl font-black text-slate-950">{{ showcaseItems[0].title }}</h3>
                <p class="mt-2 text-sm leading-6 text-slate-500">{{ showcaseItems[0].desc }}</p>
              </div>
              <RouterLink to="/generator/product-suite" class="inline-flex shrink-0 items-center gap-2 rounded-xl bg-primary px-4 py-2 text-xs font-black text-white transition-colors hover:bg-secondary">
                生成图片
                <ArrowRight class="h-4 w-4" />
              </RouterLink>
            </div>
          </article>

          <div class="grid gap-5">
            <article class="group grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm sm:grid-cols-[0.95fr_1.05fr]">
              <img :src="showcaseItems[1].image" class="h-full min-h-56 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" :alt="showcaseItems[1].title" />
              <div class="flex flex-col justify-between p-5">
                <span class="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary">服饰穿搭</span>
                <div class="mt-8">
                  <h3 class="text-lg font-black text-slate-950">{{ showcaseItems[1].title }}</h3>
                  <p class="mt-2 text-sm leading-6 text-slate-500">{{ showcaseItems[1].desc }}</p>
                </div>
              </div>
            </article>

            <article class="group grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm sm:grid-cols-[1.1fr_0.9fr]">
              <div class="flex flex-col justify-between p-5">
                <span class="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary">视频生成</span>
                <div class="mt-8">
                  <h3 class="text-lg font-black text-slate-950">{{ showcaseItems[2].title }}</h3>
                  <p class="mt-2 text-sm leading-6 text-slate-500">{{ showcaseItems[2].desc }}</p>
                </div>
              </div>
              <img :src="showcaseItems[2].image" class="h-full min-h-56 w-full object-cover transition-transform duration-500 group-hover:scale-[1.03]" :alt="showcaseItems[2].title" />
            </article>
          </div>
        </div>

        <article class="mt-5 grid overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm lg:grid-cols-[0.85fr_1.15fr]">
          <div class="flex flex-col justify-center p-6">
            <span class="w-fit rounded-full bg-primary/10 px-3 py-1 text-xs font-black text-primary">数字人与翻译</span>
            <h3 class="mt-6 text-2xl font-black text-slate-950">{{ showcaseItems[3].title }}</h3>
            <p class="mt-3 max-w-xl text-sm leading-7 text-slate-500">{{ showcaseItems[3].desc }}</p>
            <div class="mt-5 flex flex-wrap gap-2 text-xs font-bold text-slate-500">
              <span class="rounded-full bg-slate-100 px-3 py-1">口播视频</span>
              <span class="rounded-full bg-slate-100 px-3 py-1">多语言翻译</span>
              <span class="rounded-full bg-slate-100 px-3 py-1">素材复用</span>
            </div>
          </div>
          <img :src="showcaseItems[3].image" class="h-full min-h-72 w-full object-cover" :alt="showcaseItems[3].title" />
        </article>
      </section>

      <section class="bg-slate-950 px-5 py-14 text-white lg:px-8">
        <div class="mx-auto flex max-w-7xl flex-col justify-between gap-6 md:flex-row md:items-center">
          <div>
            <h2 class="text-2xl font-black">开始生成你的下一批电商内容</h2>
            <p class="mt-2 text-sm text-slate-300">图片、视频、数字人与翻译能力已经在工作台内准备好。</p>
          </div>
          <RouterLink
            :to="workspaceTarget"
            class="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-black text-white shadow-lg transition-colors hover:bg-secondary"
          >
            进入 NodePass AI
            <ArrowRight class="h-4 w-4" />
          </RouterLink>
        </div>
      </section>
    </main>
  </div>
</template>
