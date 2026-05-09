<template>
  <div class="min-h-screen flex items-center justify-center p-4 bg-gradient-to-br from-purple-100 via-white to-pink-50 dark:from-[#1a1024] dark:via-[#0b0d12] dark:to-[#16101f]">
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute -top-40 -right-40 size-96 rounded-full bg-purple-300/30 dark:bg-purple-500/10 blur-3xl"></div>
      <div class="absolute -bottom-40 -left-40 size-96 rounded-full bg-pink-300/30 dark:bg-pink-500/10 blur-3xl"></div>
    </div>

    <div class="relative w-full max-w-md surface-card p-8 shadow-[var(--shadow-lg)] animate-fade-in">
      <div class="text-center mb-6">
        <div class="inline-grid place-items-center size-14 rounded-2xl bg-gradient-to-br from-[var(--brand)] to-pink-500 text-white shadow-[var(--shadow-md)] mb-4">
          <ShieldCheck class="size-7" />
        </div>
        <h1 class="text-2xl font-semibold text-[var(--text)]">管理员登录</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">{{ siteStore.config.site_name }} · 后台管理系统</p>
      </div>

      <form class="space-y-4" @submit.prevent="handleLogin">
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">用户名</label>
          <UInput
            v-model="form.username"
            placeholder="请输入用户名"
            :prefix-icon="User"
            size="lg"
          />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">密码</label>
          <UInput
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            size="lg"
          />
        </div>

        <UButton type="submit" variant="primary" size="lg" :loading="loading" block>
          登录
        </UButton>
      </form>

      <p class="text-xs text-center text-[var(--text-muted)] mt-6">
        © {{ new Date().getFullYear() }} {{ siteStore.config.site_name }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { User, Lock, ShieldCheck } from 'lucide-vue-next'
import { UInput, UButton, toast } from '@/ui'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const siteStore = useSiteStore()

const form = ref({ username: '', password: '' })
const loading = ref(false)

const handleLogin = async () => {
  if (!form.value.username.trim() || !form.value.password) {
    toast.warning('请输入用户名和密码')
    return
  }
  try {
    loading.value = true
    await authStore.login({ username: form.value.username.trim(), password: form.value.password })
    toast.success('登录成功')
    const redirect = (route.query.redirect as string) || '/admin/dashboard'
    router.push(redirect)
  } catch (error: any) {
    if (error?.response?.status === 401) {
      toast.error('用户名或密码错误')
    } else if (error?.response?.status === 429) {
      toast.error('登录尝试过于频繁，请稍后再试')
    } else {
      toast.error('登录失败，请稍后重试')
    }
    console.error(error)
  } finally {
    loading.value = false
  }
}
</script>
