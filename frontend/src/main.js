import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

import App from './App.vue'
import { initImageCapabilities } from './constants/generator.js'
import router from './router'

async function bootstrap() {
  const app = createApp(App)

  const pinia = createPinia()
  pinia.use(piniaPluginPersistedstate)
  app.use(pinia)
  app.use(router)

  try {
    await initImageCapabilities()
  } catch (error) {
    console.error('图片能力加载失败', error)
  }

  app.mount('#app')
}

bootstrap()
