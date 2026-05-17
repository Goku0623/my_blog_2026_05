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

app.mount('#app')

import { useGuestStore } from '@/stores/guest'
import { useSiteStore } from '@/stores/site'

const guestStore = useGuestStore()
const siteStore = useSiteStore()

void guestStore.initGuest().catch((err) => console.warn('[init] guest init failed:', err))
void siteStore.fetchSiteConfig().catch((err) => console.warn('[init] site config failed:', err))

const savedTheme = localStorage.getItem('theme') || 'light'
document.documentElement.classList.toggle('dark', savedTheme === 'dark')
