<template>
  <section class="flex h-full w-[420px] shrink-0 flex-col border-r border-slate-200 bg-white">
    <div class="flex-1 overflow-y-auto">
      <slot />
    </div>
    <slot name="footer" />
  </section>
</template>
