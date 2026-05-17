<template>
  <Teleport to="body">
    <transition :enter-active-class="overlayEnterActiveClass" enter-from-class="opacity-0" enter-to-class="opacity-100"
      :leave-active-class="overlayLeaveActiveClass" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-show="visible"
        class="fixed inset-0 z-[110] cursor-pointer transform-gpu will-change-opacity motion-reduce:transition-none"
        :class="overlayClass" @click.self="closePanel">
        <div v-if="!useLiteEffects"
          class="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.06)_0%,rgba(12,14,20,0.44)_74%)]" />
        <div v-show="showCloseHint"
          class="pointer-events-none absolute right-5 top-5 size-10 rounded-full border border-white/35 bg-black/25 text-white grid place-items-center shadow-lg transition-opacity duration-300"
          :class="showCloseHint ? 'opacity-100' : 'opacity-0'">
          <CircleX class="size-5" />
        </div>
        <div
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[min(920px,calc(100vw-1rem))] h-[min(620px,calc(100vh-1rem))] rounded-2xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden will-change-transform cursor-auto transform-gpu [contain:layout_paint_size] md:w-[min(960px,calc(100vw-2rem))]"
          :class="panelClass" :style="panelStyle">
          <header class="h-14 px-4 border-b border-[var(--border)] flex items-center">
            <div class="min-w-0">
              <p class="text-sm font-semibold text-[var(--text)] truncate">AI 助手</p>
              <p class="text-xs text-[var(--text-muted)] truncate">已接入知识库问答</p>
            </div>
          </header>

          <div ref="messagesScroller"
            class="h-[calc(100%-10rem)] overflow-y-auto overscroll-contain px-4 py-3 space-y-3 [content-visibility:auto] [scrollbar-gutter:stable] [-webkit-overflow-scrolling:touch]">
            <div v-if="messages.length === 0"
              class="rounded-xl border border-dashed border-[var(--border)] bg-[var(--bg-soft)] p-4 text-sm text-[var(--text-muted)]">
              您好，我是博主的小助手。可以问我有关博客的问题。
            </div>

            <div v-if="hiddenMessagesCount > 0" class="text-center text-xs text-[var(--text-muted)] py-1">
              已自动折叠较早消息（{{ hiddenMessagesCount }} 条）
            </div>

            <div v-for="item in renderedMessages" :key="item.id" class="flex"
              :class="item.role === 'user' ? 'justify-end' : 'justify-start'">
              <div v-if="item.role === 'user'" class="max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed bg-[var(--brand)] text-white">
                {{ item.content }}
              </div>
              <div v-else class="max-w-[88%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed prose prose-sm max-w-none dark:prose-invert bg-[var(--bg-muted)] text-[var(--text)] border border-[var(--border)]">
                <div v-html="renderMarkdown(item.content)" />
              </div>
            </div>

            <div v-if="loading" class="flex justify-start">
              <div
                class="rounded-2xl px-3.5 py-2.5 text-sm bg-[var(--bg-muted)] text-[var(--text-soft)] border border-[var(--border)]">
                正在思考中...
              </div>
            </div>
          </div>

          <footer class="h-[6.5rem] border-t border-[var(--border)] px-3.5 flex items-center gap-2.5">
            <input v-model="draft" type="text" maxlength="4000" placeholder="输入你的问题，回车发送"
              class="flex-1 h-20 rounded-full border border-[var(--border)] bg-[var(--surface)] px-5 text-base text-[var(--text)] placeholder:text-[var(--text-muted)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)]/40"
              @keydown.enter.prevent="sendMessage" />
            <button
              class="h-14 px-6 rounded-full bg-gradient-to-r from-[var(--brand)] to-[var(--accent)] text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="!canSendMessage" @click="sendMessage">
              发送
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { CircleX } from 'lucide-vue-next'
import { assistantChat, type AssistantHistoryMessage } from '@/api/assistant'
import { useAuthStore } from '@/stores/auth'
import { useGuestStore } from '@/stores/guest'
import { useMarkdown } from '@/composables/useMarkdown'
import { toast } from '@/ui'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
}

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const draft = ref('')
const loading = ref(false)
const { render } = useMarkdown()

const renderMarkdown = (md: string) => render(md)
const messages = ref<ChatMessage[]>([])
const sessionId = ref<string | null>(null)
const messagesScroller = ref<HTMLElement | null>(null)
const authStore = useAuthStore()
const guestStore = useGuestStore()
const MAX_LOCAL_MESSAGES = 120
const MAX_HISTORY_MESSAGES = 30
const MAX_RENDER_MESSAGES = 80
const SEND_COOLDOWN_MS = 250
const CHAT_LOCAL_TTL_MS = 24 * 60 * 60 * 1000
const showCloseHint = ref(false)
const closeHintTimer = ref<number | null>(null)
const loadedStorageKey = ref<string | null>(null)
const bodyOriginalOverflow = ref('')
const bodyOriginalPaddingRight = ref('')
const pendingScrollRaf = ref<number | null>(null)
const pendingPersistTimeout = ref<number | null>(null)
const pendingPersistIdle = ref<number | null>(null)
const lastSendAt = ref(0)
const isBodyLocked = ref(false)
const isRateLimited = ref(false)
const isMobile = ref(false)
const prefersReducedMotion = ref(false)
const isLowEndDevice = ref(false)
const mobileViewportHeight = ref<number | null>(null)
const renderedMessages = computed(() => messages.value.slice(-MAX_RENDER_MESSAGES))
const hiddenMessagesCount = computed(() => Math.max(0, messages.value.length - renderedMessages.value.length))
const canSendMessage = computed(() => !loading.value && !isRateLimited.value && !!draft.value.trim())
const useLiteEffects = computed(() => isMobile.value || prefersReducedMotion.value || isLowEndDevice.value)
const overlayEnterActiveClass = computed(() => useLiteEffects.value
  ? 'transition duration-120 ease-out'
  : 'transition duration-180 ease-[cubic-bezier(0.2,0.8,0.2,1)]'
)
const overlayLeaveActiveClass = computed(() => useLiteEffects.value
  ? 'transition duration-90 ease-in'
  : 'transition duration-140 ease-[cubic-bezier(0.4,0,1,1)]'
)
const overlayClass = computed(() => useLiteEffects.value ? 'bg-black/42' : 'bg-black/38')
const panelClass = computed(() => {
  const motionClass = useLiteEffects.value
    ? 'transition-opacity duration-120 ease-out'
    : 'transition-[transform,opacity] duration-180 ease-[cubic-bezier(0.2,0.8,0.2,1)] shadow-[var(--shadow-lg)]'
  const stateClass = props.visible
    ? 'opacity-100 scale-100'
    : useLiteEffects.value
      ? 'opacity-0 scale-100'
      : 'opacity-0 scale-[0.988]'
  return `${motionClass} ${stateClass}`
})
const panelStyle = computed(() => {
  if (!isMobile.value || mobileViewportHeight.value === null) return {} as Record<string, string>
  return {
    height: `min(620px, calc(${mobileViewportHeight.value}px - 10px))`,
    width: 'calc(100vw - 0.75rem)',
  }
})

const getRateLimitStorageKey = () => {
  const identity = resolveSessionIdentity()
  return identity ? `assistant_rate_limited_until:${identity}` : null
}

const getTodayEndTimestamp = () => {
  const now = new Date()
  const end = new Date(now)
  end.setHours(23, 59, 59, 999)
  return end.getTime()
}

const syncRateLimitState = () => {
  const key = getRateLimitStorageKey()
  if (!key) {
    isRateLimited.value = false
    return
  }
  const raw = localStorage.getItem(key)
  const until = Number(raw || 0)
  if (Number.isFinite(until) && until > Date.now()) {
    isRateLimited.value = true
    return
  }
  localStorage.removeItem(key)
  isRateLimited.value = false
}

const markRateLimitedUntilTodayEnd = () => {
  const key = getRateLimitStorageKey()
  if (!key) {
    isRateLimited.value = true
    return
  }
  localStorage.setItem(key, String(getTodayEndTimestamp()))
  isRateLimited.value = true
}

const updateRuntimeProfile = () => {
  if (typeof window === 'undefined') return
  isMobile.value = window.matchMedia('(max-width: 768px)').matches
  prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const nav = navigator as Navigator & { deviceMemory?: number }
  const cores = typeof nav.hardwareConcurrency === 'number' ? nav.hardwareConcurrency : 8
  const memory = typeof nav.deviceMemory === 'number' ? nav.deviceMemory : 8
  isLowEndDevice.value = cores <= 4 || memory <= 4
}

const updateViewportHeight = () => {
  if (typeof window === 'undefined') return
  const visualHeight = window.visualViewport?.height
  mobileViewportHeight.value = Math.round(visualHeight ?? window.innerHeight)
}

const storageKey = () => {
  if (authStore.isAuthenticated && authStore.adminInfo?.id) {
    return `assistant_chat:admin:${authStore.adminInfo.id}`
  }
  if (guestStore.guestToken) {
    return `assistant_chat:guest:${guestStore.guestToken}`
  }
  return null
}

const resolveSessionIdentity = () => {
  if (authStore.isAuthenticated && authStore.adminInfo?.id) {
    return `admin:${authStore.adminInfo.id}`
  }
  if (guestStore.guestToken) {
    return `guest:${guestStore.guestToken}`
  }
  return null
}

const buildDailySessionId = () => {
  const identity = resolveSessionIdentity()
  if (!identity) return null
  const today = new Date()
  const datePart = `${today.getFullYear()}${String(today.getMonth() + 1).padStart(2, '0')}${String(today.getDate()).padStart(2, '0')}`
  return `${identity}:${datePart}`
}

const ensureSessionId = () => {
  const current = sessionId.value?.trim()
  if (current) return current
  const generated = buildDailySessionId()
  if (generated) {
    sessionId.value = generated
  }
  return sessionId.value
}

const flushPersistChatState = () => {
  const key = storageKey()
  if (!key) return
  const recentMessages = messages.value.slice(-MAX_LOCAL_MESSAGES)
  localStorage.setItem(
    key,
    JSON.stringify({
      session_id: sessionId.value,
      messages: recentMessages,
      updated_at: Date.now(),
    })
  )
}

const clearPendingPersist = () => {
  if (pendingPersistTimeout.value !== null) {
    clearTimeout(pendingPersistTimeout.value)
    pendingPersistTimeout.value = null
  }
  if (pendingPersistIdle.value !== null && 'cancelIdleCallback' in window) {
    ; (window as any).cancelIdleCallback(pendingPersistIdle.value)
    pendingPersistIdle.value = null
  }
}

const persistChatState = () => {
  clearPendingPersist()
  if ('requestIdleCallback' in window) {
    pendingPersistIdle.value = (window as any).requestIdleCallback(() => {
      flushPersistChatState()
      pendingPersistIdle.value = null
    }, { timeout: 300 })
    return
  }
  pendingPersistTimeout.value = setTimeout(() => {
    flushPersistChatState()
    pendingPersistTimeout.value = null
  }, 80)
}

const loadPersistedChatState = () => {
  const key = storageKey()
  if (!key) return
  if (loadedStorageKey.value === key) return
  const raw = localStorage.getItem(key)
  loadedStorageKey.value = key
  if (!raw) return
  try {
    const parsed = JSON.parse(raw)
    const updatedAt = Number(parsed?.updated_at || 0)
    if (!updatedAt || Date.now() - updatedAt > CHAT_LOCAL_TTL_MS) {
      localStorage.removeItem(key)
      messages.value = []
      sessionId.value = buildDailySessionId()
      return
    }
    const todaySessionId = buildDailySessionId()
    const parsedSessionId = typeof parsed?.session_id === 'string' ? parsed.session_id.trim() : ''
    if (todaySessionId && parsedSessionId && parsedSessionId !== todaySessionId) {
      localStorage.removeItem(key)
      messages.value = []
      sessionId.value = todaySessionId
      return
    }
    const parsedMessages = Array.isArray(parsed?.messages) ? parsed.messages : []
    messages.value = parsedMessages
      .filter((item: any) => item && (item.role === 'user' || item.role === 'assistant') && typeof item.content === 'string')
      .map((item: any) => ({
        id: typeof item.id === 'string' ? item.id : `${item.role}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
        role: item.role,
        content: item.content,
      }))
      .slice(-MAX_LOCAL_MESSAGES)
    sessionId.value = parsedSessionId || todaySessionId
  } catch {
    sessionId.value = buildDailySessionId()
  }
}

const getApiErrorMessage = (error: any, fallback: string) => {
  return error?.response?.data?.message
    || error?.response?.data?.detail
    || fallback
}

const MAINTENANCE_MESSAGE = '功能维护中，择日再来吧'

const shouldUseMaintenanceMessage = (error: any) => {
  const statusCode = Number(error?.response?.status || 0)
  if ([500, 502, 503, 504].includes(statusCode)) {
    return true
  }
  const backendMessage = String(error?.response?.data?.message || error?.response?.data?.detail || '')
  return backendMessage.includes('N8N_ASSISTANT_WEBHOOK_URL 未配置')
}

const closePanel = () => emit('close')

const clearCloseHintTimer = () => {
  if (closeHintTimer.value !== null) {
    clearTimeout(closeHintTimer.value)
    closeHintTimer.value = null
  }
}

const clearPendingScrollRaf = () => {
  if (pendingScrollRaf.value !== null) {
    window.cancelAnimationFrame(pendingScrollRaf.value)
    pendingScrollRaf.value = null
  }
}

const startCloseHintTimer = () => {
  clearCloseHintTimer()
  showCloseHint.value = true
  closeHintTimer.value = setTimeout(() => {
    showCloseHint.value = false
    closeHintTimer.value = null
  }, 2200)
}

const buildHistory = (): AssistantHistoryMessage[] => {
  return messages.value.slice(-MAX_HISTORY_MESSAGES).map((item) => ({
    role: item.role,
    content: item.content,
  }))
}

const scrollToBottom = async () => {
  await nextTick()
  if (!messagesScroller.value) return
  clearPendingScrollRaf()
  pendingScrollRaf.value = window.requestAnimationFrame(() => {
    if (!messagesScroller.value) return
    messagesScroller.value.scrollTop = messagesScroller.value.scrollHeight
    pendingScrollRaf.value = null
  })
}

const sendMessage = async () => {
  const content = draft.value.trim()
  syncRateLimitState()
  if (!content || loading.value || isRateLimited.value) {
    if (isRateLimited.value) {
      toast.warning('今日提问次数已达上限，请明天再来')
    }
    return
  }
  const ensuredSessionId = ensureSessionId()
  const now = Date.now()
  if (now - lastSendAt.value < SEND_COOLDOWN_MS) return
  lastSendAt.value = now
  const requestMessage = content
  const userMessageId = `u-${Date.now()}`
  messages.value.push({
    id: userMessageId,
    role: 'user',
    content: requestMessage,
  })
  draft.value = ''
  persistChatState()
  await scrollToBottom()

  loading.value = true
  try {
    const res = await assistantChat({
      message: requestMessage,
      session_id: ensuredSessionId,
      history: buildHistory(),
    })
    const data = res.data?.data
    const reply = data?.reply?.trim()
    if (!reply) {
      throw new Error('empty_reply')
    }
    sessionId.value = data?.session_id ?? sessionId.value
    messages.value.push({
      id: `a-${Date.now()}`,
      role: 'assistant',
      content: reply,
    })
    persistChatState()
    await scrollToBottom()
  } catch (error: any) {
    const statusCode = Number(error?.response?.status || 0)
    if (statusCode === 429) {
      messages.value = messages.value.filter((item) => item.id !== userMessageId)
      persistChatState()
      await scrollToBottom()
      markRateLimitedUntilTodayEnd()
      const message = getApiErrorMessage(error, '今日提问次数已达上限，请明天再来')
      toast.warning(message)
      return
    }
    if (shouldUseMaintenanceMessage(error)) {
      messages.value = messages.value.filter((item) => item.id !== userMessageId)
      persistChatState()
      await scrollToBottom()
      toast.error(MAINTENANCE_MESSAGE)
      return
    }
    messages.value = messages.value.filter((item) => item.id !== userMessageId)
    persistChatState()
    await scrollToBottom()
    const message = getApiErrorMessage(error, '助手暂时不可用，请稍后再试')
    toast.error(message)
  } finally {
    loading.value = false
  }
}

const lockBodyScroll = () => {
  if (isBodyLocked.value) return
  const scrollbarCompensation = window.innerWidth - document.documentElement.clientWidth
  bodyOriginalOverflow.value = document.body.style.overflow
  bodyOriginalPaddingRight.value = document.body.style.paddingRight
  document.body.style.overflow = 'hidden'
  if (scrollbarCompensation > 0) {
    document.body.style.paddingRight = `${scrollbarCompensation}px`
  }
  isBodyLocked.value = true
}

const unlockBodyScroll = () => {
  if (!isBodyLocked.value) return
  document.body.style.overflow = bodyOriginalOverflow.value
  document.body.style.paddingRight = bodyOriginalPaddingRight.value
  isBodyLocked.value = false
}

watch(
  () => props.visible,
  (value) => {
    if (value) {
      lockBodyScroll()
      syncRateLimitState()
      startCloseHintTimer()
      void scrollToBottom()
      return
    }
    unlockBodyScroll()
    clearCloseHintTimer()
    clearPendingScrollRaf()
    showCloseHint.value = false
    draft.value = ''
  }
)

watch(
  () => [authStore.isAuthenticated, authStore.adminInfo?.id, guestStore.guestToken],
  () => {
    loadedStorageKey.value = null
    syncRateLimitState()
    loadPersistedChatState()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  clearCloseHintTimer()
  clearPendingScrollRaf()
  clearPendingPersist()
  flushPersistChatState()
  unlockBodyScroll()
  if (typeof window !== 'undefined') {
    window.removeEventListener('resize', updateRuntimeProfile)
    window.removeEventListener('resize', updateViewportHeight)
    window.visualViewport?.removeEventListener('resize', updateViewportHeight)
  }
})

onMounted(() => {
  updateRuntimeProfile()
  updateViewportHeight()
  ensureSessionId()
  window.addEventListener('resize', updateRuntimeProfile, { passive: true })
  window.addEventListener('resize', updateViewportHeight, { passive: true })
  window.visualViewport?.addEventListener('resize', updateViewportHeight, { passive: true })
})
</script>
