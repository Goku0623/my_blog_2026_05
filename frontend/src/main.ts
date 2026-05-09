import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './style.css'
import 'highlight.js/styles/atom-one-dark.css'
import { installConfirm } from './ui'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
installConfirm(app)

// 立即挂载，避免接口慢导致首屏空白
app.mount('#app')

// 后台异步初始化游客身份与站点配置（不阻塞渲染）
import { useGuestStore } from '@/stores/guest'
import { useSiteStore } from '@/stores/site'

const guestStore = useGuestStore()
const siteStore = useSiteStore()

void guestStore.initGuest().catch((err) => console.warn('[init] guest init failed:', err))
void siteStore.fetchSiteConfig().catch((err) => console.warn('[init] site config failed:', err))

// 主题：从 localStorage 读取（默认 light）
const savedTheme = localStorage.getItem('theme') || 'light'
document.documentElement.classList.toggle('dark', savedTheme === 'dark')
