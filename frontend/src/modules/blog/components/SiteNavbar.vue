<template>
  <header :class="[
    'sticky top-0 z-40 transition-[background,backdrop-filter,border-color] duration-300',
    scrolled ? 'glass nav-floating border-b border-[var(--border)]' : 'border-b border-transparent bg-transparent',
  ]">
    <div class="container-page h-16 sm:h-[72px]">
      <div class="flex h-full items-center justify-between gap-4">
        <!-- Logo -->
        <router-link to="/" class="flex min-w-0 items-center gap-3 shrink-0 group">
          <span
            class="relative grid place-items-center size-9 sm:size-10 rounded-xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white font-bold text-sm shadow-[var(--shadow-md)] ring-1 ring-white/30 dark:ring-white/10 transition-transform duration-300 group-hover:scale-[1.04]">
            {{ initialChar }}
            <span
              class="absolute -inset-2 rounded-2xl bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] opacity-0 blur-xl transition-opacity duration-500 group-hover:opacity-30"></span>
          </span>
          <span class="hidden sm:flex flex-col leading-tight">
            <span class="truncate text-[15px] font-semibold tracking-tight text-[var(--text)]">
              {{ siteStore.config.site_name }}
            </span>
            <span class="truncate text-[11px] text-[var(--text-muted)] tracking-[0.18em] uppercase">
              Blog · Notes · Code
            </span>
          </span>
        </router-link>

        <!-- 中间菜单（桌面端居中） -->
        <nav
          class="hidden lg:flex absolute left-1/2 -translate-x-1/2 items-center gap-1 p-1 rounded-full border border-[var(--border)] bg-[var(--surface)]/70 backdrop-blur-md shadow-[var(--shadow-sm)]">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to" :class="[
            'relative px-4 py-1.5 text-sm font-medium rounded-full transition-colors duration-200',
            isActive(item.to)
              ? 'text-[var(--text)] bg-[var(--bg-muted)] shadow-[var(--shadow-sm)]'
              : 'text-[var(--text-soft)] hover:text-[var(--text)]',
          ]">
            {{ item.label }}
          </router-link>
        </nav>

        <!-- 右侧操作 -->
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          <!-- 搜索按钮（命令风格） -->
          <router-link to="/search"
            class="hidden md:inline-flex items-center gap-2 h-9 pl-3 pr-2 rounded-full border border-[var(--border)] bg-[var(--surface)]/60 text-[13px] text-[var(--text-muted)] hover:text-[var(--text)] hover:border-[var(--border-strong)] transition-colors min-w-[160px]">
            <Search class="size-3.5" />
            <span class="flex-1 text-left">搜索文章…</span>
            <kbd
              class="text-[10px] px-1.5 py-0.5 rounded border border-[var(--border)] text-[var(--text-muted)] bg-[var(--bg-muted)]">⌘
              K</kbd>
          </router-link>

          <!-- 移动端搜索 -->
          <router-link to="/search"
            class="md:hidden size-9 rounded-full grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            aria-label="搜索">
            <Search class="size-4" />
          </router-link>

          <!-- 主题切换 -->
          <button
            class="size-9 rounded-full grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            @click="toggleTheme" :aria-label="isDark ? '切换为亮色' : '切换为暗色'">
            <Sun v-if="isDark" class="size-4" />
            <Moon v-else class="size-4" />
          </button>

          <!-- 后台入口 -->
          <router-link to="/admin"
            class="hidden sm:inline-flex h-9 px-3 items-center gap-1.5 rounded-full text-[13px] font-medium text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            aria-label="后台">
            <Settings class="size-4" />
            <span class="hidden lg:inline">后台</span>
          </router-link>

          <!-- 移动端菜单按钮 -->
          <button
            class="lg:hidden size-9 rounded-full grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
            aria-label="菜单" @click="mobileMenuOpen = !mobileMenuOpen">
            <Menu v-if="!mobileMenuOpen" class="size-4" />
            <X v-else class="size-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- 移动端展开菜单 -->
    <transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0" leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="mobileMenuOpen"
        class="lg:hidden border-t border-[var(--border)] bg-[var(--surface)]/95 backdrop-blur-md">
        <nav class="container-page py-3 grid gap-1">
          <router-link v-for="item in navItems" :key="item.to" :to="item.to"
            class="px-3 py-2.5 rounded-xl text-sm font-medium transition-colors" :class="isActive(item.to)
              ? 'text-[var(--brand)] bg-[var(--brand-soft)]'
              : 'text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)]'"
            @click="mobileMenuOpen = false">
            {{ item.label }}
          </router-link>
        </nav>
      </div>
    </transition>

    <Teleport to="body">
      <router-link v-if="showHomeRocket" to="/" aria-label="返回首页"
        class="fixed right-10 bottom-10 z-[90] inline-flex size-18 items-center justify-center rounded-full bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] text-white shadow-[var(--shadow-lg)] transition-all hover:scale-[1.06] hover:shadow-[var(--shadow-xl)] active:scale-95">
        <Rocket class="size-7" />
      </router-link>
    </Teleport>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Sun, Moon, Settings, Search, Menu, X, Rocket } from 'lucide-vue-next'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()
const route = useRoute()
const router = useRouter()

const navItems = [
  { to: '/', label: '首页' },
  { to: '/messages', label: '留言墙' },
  { to: '/about', label: '关于我' },
]

const showHomeRocket = computed(() => route.path !== '/')

const initialChar = computed(() => Array.from(siteStore.config.site_name || 'B')[0]?.toUpperCase() ?? 'B')

const isActive = (to: string) => {
  if (to === '/') return route.path === '/'
  return route.path.startsWith(to)
}

const isDark = ref(false)
const toggleTheme = () => {
  const next = !isDark.value
  isDark.value = next
  document.documentElement.classList.toggle('dark', next)
  localStorage.setItem('theme', next ? 'dark' : 'light')
}

const scrolled = ref(false)
const mobileMenuOpen = ref(false)
let scrollRafId: number | null = null

const handleScroll = () => {
  if (scrollRafId !== null) return
  scrollRafId = window.requestAnimationFrame(() => {
    scrollRafId = null
    scrolled.value = window.scrollY > 4
  })
}

const handleKey = (e: KeyboardEvent) => {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    if (route.path !== '/search') {
      router.push('/search')
    }
  }
}

watch(() => route.fullPath, () => {
  mobileMenuOpen.value = false
})

onMounted(() => {
  isDark.value = document.documentElement.classList.contains('dark')
  handleScroll()
  window.addEventListener('scroll', handleScroll, { passive: true })
  window.addEventListener('keydown', handleKey)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('keydown', handleKey)
  if (scrollRafId !== null) {
    window.cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
})
</script>
