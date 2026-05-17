<template>
  <div class="flex min-h-screen bg-[var(--bg-soft)] text-[var(--text)]">
    <!-- 侧边栏 -->
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-40 flex flex-col border-r border-[var(--border)] bg-[var(--surface)] transition-[width,transform] duration-200',
        collapsed ? 'w-16' : 'w-60',
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
    >
      <div class="h-16 flex items-center gap-2 border-b border-[var(--border)] px-4 shrink-0">
        <span class="grid place-items-center size-9 rounded-xl bg-gradient-to-br from-[var(--brand)] to-pink-500 text-white font-bold shadow-[var(--shadow-sm)] overflow-hidden">
          <img v-if="authStore.adminInfo?.avatar" :src="authStore.adminInfo.avatar" class="size-full object-cover" alt="" />
          <span v-else>A</span>
        </span>
        <span v-if="!collapsed" class="font-semibold text-[var(--text)] truncate">管理后台</span>
      </div>

      <nav class="flex-1 overflow-y-auto py-3 space-y-0.5">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="[
            'group flex items-center gap-3 mx-2 px-3 py-2 rounded-lg text-sm transition-colors',
            isActive(item.path)
              ? 'bg-[var(--brand)]/12 text-[var(--brand)] font-medium'
              : 'text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)]',
          ]"
        >
          <component :is="item.icon" class="size-4 shrink-0" />
          <span v-if="!collapsed" class="truncate">{{ item.label }}</span>
        </router-link>
      </nav>

      <button
        type="button"
        class="hidden lg:flex items-center gap-2 mx-2 mb-3 px-3 py-2 rounded-lg text-sm text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)]"
        @click="collapsed = !collapsed"
      >
        <PanelLeftClose v-if="!collapsed" class="size-4" />
        <PanelLeftOpen v-else class="size-4" />
        <span v-if="!collapsed">收起菜单</span>
      </button>
    </aside>

    <!-- 移动端遮罩 -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-30 bg-black/30 lg:hidden"
      @click="sidebarOpen = false"
    />

    <!-- 主区 -->
    <div class="flex-1 min-w-0 flex flex-col">
      <header class="sticky top-0 z-20 h-16 flex items-center justify-between gap-3 border-b border-[var(--border)] bg-[var(--surface)]/85 backdrop-blur px-4 sm:px-6">
        <div class="flex items-center gap-3 min-w-0">
          <button
            class="lg:hidden size-9 rounded-lg grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
            @click="sidebarOpen = true"
          >
            <Menu class="size-4" />
          </button>
          <nav class="flex items-center gap-1.5 text-sm text-[var(--text-soft)]">
            <router-link to="/admin/dashboard" class="hover:text-[var(--brand)]">首页</router-link>
            <span v-if="route.name !== 'Dashboard'" class="text-[var(--text-muted)]">/</span>
            <span v-if="route.name !== 'Dashboard'" class="text-[var(--text)] truncate">{{ route.meta.title as string }}</span>
          </nav>
        </div>

        <div class="flex items-center gap-2">
          <button
            class="size-9 rounded-lg grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
            @click="toggleTheme"
            :title="isDark ? '切换为亮色' : '切换为暗色'"
          >
            <Sun v-if="isDark" class="size-4" />
            <Moon v-else class="size-4" />
          </button>

          <div ref="notifRef" class="relative">
            <button
              class="size-9 rounded-lg grid place-items-center text-[var(--text-soft)] hover:bg-[var(--bg-muted)] relative"
              @click="toggleNotif"
            >
              <Bell class="size-4" />
              <span
                v-if="unreadCount > 0"
                class="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] grid place-items-center rounded-full bg-red-500 text-white text-[10px] font-bold px-1 leading-none"
              >{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
            </button>
            <Transition name="fade">
              <div
                v-if="notifOpen"
                class="absolute right-0 mt-2 w-80 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-lg)] z-50 max-h-[420px] flex flex-col"
              >
                <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--border)] shrink-0">
                  <span class="text-sm font-semibold text-[var(--text)]">消息通知</span>
                  <button
                    v-if="unreadCount > 0"
                    class="text-xs text-[var(--brand)] hover:underline"
                    @click="handleMarkAllRead"
                  >全部已读</button>
                </div>
                <div class="flex-1 overflow-y-auto">
                  <div v-if="notifications.length === 0" class="px-4 py-8 text-center text-sm text-[var(--text-muted)]">
                    暂无通知
                  </div>
                  <button
                    v-for="item in notifications"
                    :key="item.id"
                    class="w-full text-left px-4 py-3 border-b border-[var(--border)] last:border-b-0 hover:bg-[var(--bg-muted)] transition-colors"
                    @click="handleNotifClick(item)"
                  >
                    <div class="flex items-start gap-2">
                      <span
                        v-if="!item.is_read"
                        class="mt-1.5 size-2 rounded-full bg-[var(--brand)] shrink-0"
                      />
                      <span v-else class="mt-1.5 size-2 shrink-0" />
                      <div class="min-w-0 flex-1">
                        <p class="text-sm text-[var(--text)] line-clamp-2">{{ item.title }}</p>
                        <p class="text-xs text-[var(--text-muted)] mt-0.5">{{ formatNotifTime(item.created_at) }}</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </Transition>
          </div>

          <a
            class="hidden sm:inline-flex h-9 items-center gap-1.5 px-3 rounded-lg text-sm text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
            href="/" target="_blank"
          >
            <ExternalLink class="size-4" />
            <span>访问站点</span>
          </a>

          <div ref="userMenuRef" class="relative">
            <button
              type="button"
              class="flex items-center gap-2 h-9 pl-1.5 pr-2 rounded-lg hover:bg-[var(--bg-muted)]"
              @click="dropdownOpen = !dropdownOpen"
            >
              <UAvatar :src="authStore.adminInfo?.avatar || undefined" :name="adminName" :size="28" />
              <span class="hidden sm:block text-sm">{{ adminName }}</span>
              <ChevronDown class="size-4 text-[var(--text-muted)]" />
            </button>
            <Transition name="fade">
              <div
                v-if="dropdownOpen"
                class="absolute right-0 mt-2 w-44 rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-lg)] py-1.5 z-50"
              >
                <div class="px-3 py-2 border-b border-[var(--border)]">
                  <p class="text-sm font-medium text-[var(--text)] truncate">{{ adminName }}</p>
                  <p class="text-xs text-[var(--text-muted)] truncate">{{ authStore.adminInfo?.email || '管理员' }}</p>
                </div>
                <button
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
                  @click="openProfileModal"
                >
                  个人资料
                </button>
                <button
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
                  @click="openPasswordModal"
                >
                  修改密码
                </button>
                <button
                  type="button"
                  class="w-full flex items-center gap-2 px-3 py-2 text-sm text-[var(--text-soft)] hover:bg-[var(--bg-muted)]"
                  @click="handleLogout"
                >
                  <LogOut class="size-4" /> 退出登录
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </header>

      <main class="flex-1 p-4 sm:p-6">
        <router-view v-slot="{ Component, route: viewRoute }">
          <transition name="fade">
            <keep-alive
              v-if="viewRoute.meta.keepAlive"
              :include="keepAliveInclude"
              :max="3"
            >
              <component
                :is="Component"
                :key="viewRoute.name as string"
              />
            </keep-alive>
            <component
              :is="Component"
              v-else
              :key="viewRoute.path"
            />
          </transition>
        </router-view>
      </main>
    </div>

    <UModal v-model="profileVisible" title="个人资料" width="sm" :backdrop-blur="false">
      <div class="space-y-4">
        <div class="flex flex-col items-center gap-3">
          <UAvatar :src="avatarPreview || authStore.adminInfo?.avatar || undefined" :name="profileForm.username" :size="72" />
          <div class="flex gap-2">
            <input ref="avatarInputRef" type="file" accept="image/*" class="hidden" @change="handleAvatarFileChange" />
            <UButton variant="outline" size="sm" @click="avatarInputRef?.click()">
              <template #icon><Camera class="size-4" /></template>
              上传头像
            </UButton>
            <UButton v-if="avatarPreview" variant="ghost" size="sm" @click="clearAvatar">清除</UButton>
          </div>
        </div>
        <div class="space-y-1.5">
          <label class="text-sm text-[var(--text-soft)]">用户名</label>
          <UInput v-model="profileForm.username" placeholder="请输入用户名" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm text-[var(--text-soft)]">邮箱</label>
          <UInput v-model="profileForm.email" placeholder="请输入邮箱（可选）" />
        </div>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="profileVisible = false">取消</UButton>
          <UButton variant="primary" :loading="savingProfile" @click="handleSaveProfile">保存</UButton>
        </div>
      </div>
    </UModal>

    <UModal v-model="passwordVisible" title="修改密码" width="sm" :backdrop-blur="false">
      <div class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm text-[var(--text-soft)]">当前密码</label>
          <UInput v-model="passwordForm.old_password" type="password" placeholder="请输入当前密码" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm text-[var(--text-soft)]">新密码</label>
          <UInput v-model="passwordForm.new_password" type="password" placeholder="请输入新密码" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm text-[var(--text-soft)]">确认新密码</label>
          <UInput v-model="passwordForm.confirm_password" type="password" placeholder="请再次输入新密码" />
        </div>
        <div class="flex justify-end gap-2">
          <UButton variant="ghost" @click="passwordVisible = false">取消</UButton>
          <UButton variant="primary" :loading="savingPassword" @click="handleChangePassword">确认修改</UButton>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { changePassword, updateAdminProfile } from '@/api/auth'
import {
  LayoutDashboard, FileText, FolderTree, Tags, MessageSquare, StickyNote,
  Settings, BarChart3, ShieldAlert, History,
  Menu, ChevronDown, LogOut, Sun, Moon, ExternalLink,
  PanelLeftClose, PanelLeftOpen, Camera, Bell,
} from 'lucide-vue-next'
import { UAvatar, UModal, UInput, UButton, confirmDialog, toast } from '@/ui'
import {
  getNotifications, getUnreadNotificationCount,
  markNotificationRead, markAllNotificationsRead,
  type AdminNotification,
} from '@/api/system'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const navItems = [
  { path: '/admin/dashboard', label: '仪表盘', icon: LayoutDashboard },
  { path: '/admin/articles', label: '文章管理', icon: FileText },
  { path: '/admin/categories', label: '分类管理', icon: FolderTree },
  { path: '/admin/tags', label: '标签管理', icon: Tags },
  { path: '/admin/comments', label: '评论管理', icon: MessageSquare },
  { path: '/admin/guestbook', label: '留言管理', icon: StickyNote },
  { path: '/admin/statistics', label: '数据统计', icon: BarChart3 },
  { path: '/admin/sensitive-words', label: '敏感词', icon: ShieldAlert },
  { path: '/admin/operation-logs', label: '操作日志', icon: History },
  { path: '/admin/system-config', label: '系统配置', icon: Settings },
]
const keepAliveInclude = ['Articles', 'Comments', 'OperationLogs']

const collapsed = ref(localStorage.getItem('admin_sidebar_collapsed') === '1')
const sidebarOpen = ref(false)
const dropdownOpen = ref(false)
const profileVisible = ref(false)
const passwordVisible = ref(false)
const savingProfile = ref(false)
const savingPassword = ref(false)
const profileForm = ref({
  username: '',
  email: '',
})
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarPreview = ref<string | null>(null)
const avatarDataUrl = ref<string | null>(null)
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: '',
})
const userMenuRef = ref<HTMLElement | null>(null)
const notifRef = ref<HTMLElement | null>(null)
const notifOpen = ref(false)
const unreadCount = ref(0)
const notifications = ref<AdminNotification[]>([])

const isDark = ref(document.documentElement.classList.contains('dark'))
const toggleTheme = () => {
  const next = !isDark.value
  isDark.value = next
  document.documentElement.classList.toggle('dark', next)
  localStorage.setItem('theme', next ? 'dark' : 'light')
}

const adminName = computed(() => authStore.adminInfo?.username || 'Admin')
const isActive = (path: string) => route.path.startsWith(path)

watch(collapsed, (v) => localStorage.setItem('admin_sidebar_collapsed', v ? '1' : '0'))

const handleLogout = async () => {
  dropdownOpen.value = false
  const ok = await confirmDialog({
    title: '退出登录',
    message: '确定要退出当前账号吗？',
    confirmText: '退出',
    danger: true,
  })
  if (!ok) return
  await authStore.logout()
  toast.success('已退出登录')
  router.push('/admin/login')
}

const openProfileModal = () => {
  dropdownOpen.value = false
  profileForm.value.username = authStore.adminInfo?.username || ''
  profileForm.value.email = authStore.adminInfo?.email || ''
  avatarPreview.value = null
  avatarDataUrl.value = null
  profileVisible.value = true
}

const compressAvatar = async (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const img = new Image()
      img.onload = () => {
        const canvas = document.createElement('canvas')
        const size = 200
        canvas.width = size
        canvas.height = size
        const ctx = canvas.getContext('2d')
        if (!ctx) { reject(new Error('canvas unavailable')); return }
        const minDim = Math.min(img.width, img.height)
        const sx = (img.width - minDim) / 2
        const sy = (img.height - minDim) / 2
        ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, size, size)
        resolve(canvas.toDataURL('image/jpeg', 0.85))
      }
      img.onerror = () => reject(new Error('load image failed'))
      img.src = reader.result as string
    }
    reader.onerror = () => reject(new Error('read file failed'))
    reader.readAsDataURL(file)
  })
}

const handleAvatarFileChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const dataUrl = await compressAvatar(file)
    avatarDataUrl.value = dataUrl
    avatarPreview.value = dataUrl
  } catch {
    toast.error('图片处理失败')
  }
  input.value = ''
}

const clearAvatar = () => {
  avatarDataUrl.value = ''
  avatarPreview.value = null
}

const handleSaveProfile = async () => {
  const username = profileForm.value.username.trim()
  const email = profileForm.value.email.trim()
  if (!username) {
    toast.warning('用户名不能为空')
    return
  }

  try {
    savingProfile.value = true
    const payload: { username: string; email?: string; avatar?: string | null } = { username, email: email || undefined }
    if (avatarDataUrl.value !== null) {
      payload.avatar = avatarDataUrl.value || null
    }
    await updateAdminProfile(payload)
    await authStore.fetchAdminInfo()
    localStorage.setItem('admin_profile_updated_at', String(Date.now()))
    window.dispatchEvent(new CustomEvent('admin-profile-updated'))
    profileVisible.value = false
    toast.success('个人资料已更新')
  } catch (error: any) {
    const message = error?.response?.data?.message || '更新个人资料失败'
    toast.error(message)
  } finally {
    savingProfile.value = false
  }
}

const openPasswordModal = () => {
  dropdownOpen.value = false
  passwordForm.value.old_password = ''
  passwordForm.value.new_password = ''
  passwordForm.value.confirm_password = ''
  passwordVisible.value = true
}

const handleChangePassword = async () => {
  const oldPassword = passwordForm.value.old_password
  const newPassword = passwordForm.value.new_password
  const confirmPassword = passwordForm.value.confirm_password

  if (!oldPassword || !newPassword || !confirmPassword) {
    toast.warning('请完整填写密码信息')
    return
  }
  if (newPassword.length < 6) {
    toast.warning('新密码至少 6 位')
    return
  }
  if (newPassword !== confirmPassword) {
    toast.warning('两次输入的新密码不一致')
    return
  }

  try {
    savingPassword.value = true
    await changePassword({ old_password: oldPassword, new_password: newPassword })
    passwordVisible.value = false
    toast.success('密码修改成功，请重新登录')
    await authStore.logout()
    router.push('/admin/login')
  } catch (error: any) {
    const message = error?.response?.data?.message || '修改密码失败'
    toast.error(message)
  } finally {
    savingPassword.value = false
  }
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!userMenuRef.value?.contains(target)) dropdownOpen.value = false
  if (!notifRef.value?.contains(target)) notifOpen.value = false
}

const formatNotifTime = (iso: string) => {
  const d = new Date(iso)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return '刚刚'
  if (mins < 60) return `${mins} 分钟前`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours} 小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} 天前`
  return d.toLocaleDateString('zh-CN')
}

const toggleNotif = () => {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) fetchNotifications()
}

const fetchUnreadCount = async () => {
  try {
    const res = await getUnreadNotificationCount()
    unreadCount.value = res.data?.data?.count ?? 0
  } catch { /* ignore */ }
}

const fetchNotifications = async () => {
  try {
    const res = await getNotifications(1, 5)
    const data = res.data?.data
    if (data) {
      notifications.value = data.items.filter((n) => !n.is_read)
      unreadCount.value = data.items.filter((n) => !n.is_read).length
    }
  } catch { /* ignore */ }
}

const handleNotifClick = async (item: AdminNotification) => {
  if (!item.is_read) {
    try {
      await markNotificationRead(item.id)
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch { /* ignore */ }
  }
  notifications.value = notifications.value.filter((n) => n.id !== item.id)
  notifOpen.value = false
  if (item.link) {
    router.push(item.link)
  }
}

const handleMarkAllRead = async () => {
  try {
    await markAllNotificationsRead()
    notifications.value = []
    unreadCount.value = 0
  } catch { /* ignore */ }
}

let notifPollTimer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
  fetchUnreadCount()
  notifPollTimer = setInterval(fetchUnreadCount, 30000)
})
onBeforeUnmount(() => {
  document.removeEventListener('mousedown', handleClickOutside)
  if (notifPollTimer) clearInterval(notifPollTimer)
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}
.fade-leave-to {
  opacity: 0;
}
</style>
