<script setup>
import { computed, ref } from 'vue'
import { CheckCircle2, ImagePlus, Trash2, X } from 'lucide-vue-next'

const props = defineProps({
  images: {
    type: Array,
    required: true,
  },
  mainIndex: {
    type: Number,
    default: 0,
  },
  title: {
    type: String,
    default: '商品详情图',
  },
  maxCount: {
    type: Number,
    default: 3,
  },
  addText: {
    type: String,
    default: '添加图片',
  },
  hintText: {
    type: String,
    default: '拖拽或点击',
  },
  altText: {
    type: String,
    default: '商品',
  },
  mainBadgeText: {
    type: String,
    default: '主',
  },
  limitMessage: {
    type: String,
    default: '最多只能上传 3 张商品图',
  },
})

const emit = defineEmits(['update:images', 'update:mainIndex', 'notify'])

const fileInput = ref(null)
const dragOver = ref(false)
const placeholderCount = computed(() => Math.max(0, props.maxCount - props.images.length - 1))

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(event) {
  processFiles(Array.from(event.target.files || []))
  event.target.value = ''
}

function handleDrop(event) {
  dragOver.value = false
  processFiles(Array.from(event.dataTransfer.files || []))
}

function processFiles(files) {
  const imageFiles = files.filter((file) => file.type.startsWith('image/'))
  const limit = props.maxCount - props.images.length
  const toProcess = imageFiles.slice(0, limit)

  if (limit <= 0) {
    emit('notify', props.limitMessage)
    return
  }

  if (imageFiles.length > toProcess.length) {
    emit('notify', `已达到 ${props.maxCount} 张上限，多余图片未添加`)
  }

  Promise.all(
    toProcess.map((file) => {
      return new Promise((resolve) => {
        const reader = new FileReader()
        reader.onload = (readerEvent) => resolve(readerEvent.target.result)
        reader.readAsDataURL(file)
      })
    }),
  ).then((imageUrls) => {
    emit('update:images', [...props.images, ...imageUrls])
  })
}

function removeImage(index) {
  const nextImages = props.images.filter((_, imageIndex) => imageIndex !== index)
  emit('update:images', nextImages)

  if (props.mainIndex >= nextImages.length) {
    emit('update:mainIndex', Math.max(0, nextImages.length - 1))
  } else if (index < props.mainIndex) {
    emit('update:mainIndex', props.mainIndex - 1)
  }
}

function clearImages() {
  emit('update:images', [])
  emit('update:mainIndex', 0)
}
</script>

<template>
  <section class="border-b border-slate-100 bg-slate-50/40 p-5">
    <div class="mb-3 flex items-center justify-between">
      <label class="flex items-center gap-1.5 text-xs font-bold text-slate-700">
        <span class="h-1.5 w-1.5 rounded-full bg-primary"></span>
        {{ title }}
        <span class="font-normal text-slate-400">(支持最多 {{ maxCount }} 张，已选 {{ images.length }}/{{ maxCount }})</span>
      </label>
      <button v-if="images.length > 0" type="button" class="text-xs text-slate-400 transition-colors hover:text-rose-500" @click="clearImages">
        清空
      </button>
    </div>

    <div class="grid grid-cols-3 gap-3">
      <div
        v-for="(img, index) in images"
        :key="`${img}-${index}`"
        class="group relative flex aspect-square items-center justify-center overflow-hidden rounded-xl border border-slate-200 bg-slate-50 p-1 shadow-inner"
      >
        <img :src="img" class="max-h-full max-w-full rounded-lg object-contain transition-transform duration-300 group-hover:scale-105" :alt="altText" />
        <div class="absolute inset-0 flex items-center justify-center gap-1.5 bg-slate-900/60 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            type="button"
            class="rounded border border-slate-100 bg-white p-1.5 text-xs text-slate-800 shadow transition-colors hover:bg-slate-100"
            :class="index === mainIndex ? 'border-primary text-primary' : ''"
            title="设为渲染主图"
            @click="emit('update:mainIndex', index)"
          >
            <CheckCircle2 class="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            class="rounded border border-slate-100 bg-white p-1.5 text-rose-500 shadow transition-colors hover:bg-rose-50"
            title="删除"
            @click="removeImage(index)"
          >
            <Trash2 class="h-3.5 w-3.5" />
          </button>
        </div>
        <span v-if="index === mainIndex" class="absolute bottom-1 right-1 rounded bg-primary px-1.5 py-0.5 text-xs font-bold text-white shadow-sm">
          {{ mainBadgeText }}
        </span>
      </div>

      <button
        v-if="images.length < maxCount"
        type="button"
        class="flex aspect-square cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed p-2 transition-all duration-300"
        :class="dragOver ? 'border-primary bg-primary/10 shadow-sm' : 'border-slate-300 bg-slate-50 hover:border-slate-400 hover:bg-slate-100/50'"
        @click="triggerFileInput"
        @dragover.prevent="dragOver = true"
        @dragleave.prevent="dragOver = false"
        @drop.prevent="handleDrop"
      >
        <ImagePlus class="mb-1 h-5 w-5 text-slate-400" />
        <span class="text-center text-xs font-semibold text-slate-500">{{ addText }}</span>
        <span class="mt-0.5 text-center text-xs text-slate-400">{{ hintText }}</span>
        <input ref="fileInput" type="file" accept="image/*" class="hidden" multiple @change="handleFileChange" />
      </button>

      <div v-for="slotIndex in placeholderCount" :key="slotIndex" class="hidden aspect-square rounded-xl border border-slate-100 bg-slate-50/40 sm:block">
        <X class="m-auto mt-[40%] h-4 w-4 text-slate-200" />
      </div>
    </div>
  </section>
</template>
