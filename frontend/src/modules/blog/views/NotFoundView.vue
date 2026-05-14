<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />
    <main class="flex-1 container-page py-20 sm:py-28">
      <div class="mx-auto max-w-2xl text-center rounded-3xl border border-[var(--border)] bg-[var(--surface)] p-8 sm:p-12 shadow-[var(--shadow-sm)]">
        <p class="eyebrow">404</p>
        <h1 class="mt-4 font-display text-3xl sm:text-4xl font-bold text-[var(--text)]">页面不存在</h1>
        <p class="mt-4 text-sm sm:text-base text-[var(--text-soft)]">
          你访问的页面可能已被移动、删除，或链接地址有误。
        </p>
        <div class="mt-8 flex items-center justify-center gap-3">
          <router-link
            to="/"
            class="inline-flex items-center h-10 px-5 rounded-full bg-[var(--text)] text-[var(--bg)] text-sm font-medium hover:opacity-90 transition-opacity"
          >
            返回首页
          </router-link>
          <router-link
            to="/search"
            class="inline-flex items-center h-10 px-5 rounded-full border border-[var(--border)] text-sm font-medium text-[var(--text-soft)] hover:text-[var(--text)] hover:border-[var(--border-strong)] transition-colors"
          >
            去搜索
          </router-link>
        </div>
      </div>
    </main>
    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'
</script>
