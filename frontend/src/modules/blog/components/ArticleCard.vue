<template>
  <!-- ===================== Featured 大卡片（首页置顶） ===================== -->
  <article
    v-if="variant === 'featured'"
    class="group relative overflow-hidden rounded-3xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-md)] hover:shadow-[var(--shadow-xl)] transition-all duration-500"
  >
    <router-link :to="`/article/${article.slug}`" class="block">
      <div class="grid lg:grid-cols-2 min-h-[320px]">
        <!-- 左：图片 / 渐变占位 -->
        <div class="relative overflow-hidden lg:order-2 aspect-[16/9] lg:aspect-auto">
          <img
            v-if="coverThumb"
            :src="coverThumb"
            :alt="article.title"
            loading="lazy"
            decoding="async"
            class="absolute inset-0 size-full object-cover transition-transform duration-700 group-hover:scale-[1.04]"
          />
          <div
            v-else
            class="absolute inset-0 bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)]"
          >
            <div class="absolute inset-0 opacity-40 mix-blend-overlay"
              style="background-image: radial-gradient(circle at 30% 20%, white 0%, transparent 50%), radial-gradient(circle at 70% 80%, rgb(255,255,255,0.6) 0%, transparent 60%);">
            </div>
            <div class="absolute inset-0 grid place-items-center">
              <p class="font-display text-7xl font-bold text-white/90 tracking-tight">
                {{ article.title?.charAt(0) || '·' }}
              </p>
            </div>
          </div>
          <span class="absolute top-4 left-4 inline-flex items-center gap-1.5 rounded-full bg-black/40 backdrop-blur px-3 py-1 text-[11px] font-medium text-white">
            <Star class="size-3 fill-current text-amber-300" /> 精选
          </span>
        </div>

        <!-- 右：内容 -->
        <div class="lg:order-1 flex flex-col justify-between gap-6 p-6 sm:p-8 lg:p-10">
          <div class="space-y-4">
            <div class="flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)]">
              <span v-if="article.category" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--brand-soft)] text-[var(--brand)] font-medium">
                <Folder class="size-3" />
                {{ article.category.name }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Calendar class="size-3" /> {{ formatFriendlyTime(article.created_at) }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Eye class="size-3" /> {{ formatNumber(article.view_count ?? 0) }}
              </span>
            </div>
            <h2 class="font-display text-3xl sm:text-4xl font-bold tracking-tight text-[var(--text)] leading-[1.15] line-clamp-3">
              <span class="link-underline">{{ article.title }}</span>
            </h2>
            <p
              v-if="article.summary"
              class="text-[15px] sm:text-base text-[var(--text-soft)] leading-relaxed line-clamp-3"
            >
              {{ article.summary }}
            </p>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-4 pt-2">
            <div class="flex flex-wrap items-center gap-1.5">
              <span
                v-for="tag in (article.tags ?? []).slice(0, 3)"
                :key="tag.id"
                class="px-2 py-0.5 text-[11px] rounded-md text-[var(--text-soft)] border border-[var(--border)]"
              >
                #{{ tag.name }}
              </span>
            </div>
            <span class="inline-flex items-center gap-1 text-sm font-medium text-[var(--brand)] group-hover:gap-2 transition-all">
              阅读全文 <ArrowRight class="size-4" />
            </span>
          </div>
        </div>
      </div>
    </router-link>
  </article>

  <!-- ===================== Compact 紧凑型（侧栏 / 推荐） ===================== -->
  <router-link
    v-else-if="variant === 'compact'"
    :to="`/article/${article.slug}`"
    class="group flex items-start gap-3 py-2.5"
  >
    <span class="mt-1.5 inline-block size-1.5 shrink-0 rounded-full bg-[var(--brand)]/60 group-hover:bg-[var(--brand)] transition-colors"></span>
    <div class="min-w-0 flex-1">
      <h4 class="text-sm font-medium leading-snug text-[var(--text-soft)] group-hover:text-[var(--brand)] transition-colors line-clamp-2">
        {{ article.title }}
      </h4>
      <p class="mt-1 text-[11px] text-[var(--text-muted)]">
        {{ formatFriendlyTime(article.created_at) }}
      </p>
    </div>
  </router-link>

  <!-- ===================== Default 默认杂志式卡片 ===================== -->
  <!--
    高度由父级 .article-list-grid 的 grid-auto-rows:440px 固定，
    h-full 填满行高，内部 grid-rows 再分成封面200px + 内容区其余。
  -->
  <article
    v-else
    class="group relative grid h-full w-full min-w-0 max-w-full justify-self-stretch self-stretch grid-cols-1 grid-rows-[200px_minmax(0,1fr)] overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] transition-all duration-300 hover:-translate-y-1 hover:border-[var(--brand)]/40 hover:shadow-[var(--shadow-lg)]"
  >
    <!-- 封面：占据 grid 第一行（200px），图片绝对填满，overflow-hidden 阻止溢出 -->
    <router-link
      :to="`/article/${article.slug}`"
      class="relative block h-full w-full overflow-hidden bg-[var(--bg-muted)]"
    >
      <img
        v-if="coverThumb"
        :src="coverThumb"
        :alt="article.title"
        loading="lazy"
        decoding="async"
        class="absolute inset-0 block h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.06]"
      />
      <div
        v-else
        class="absolute inset-0 bg-gradient-to-br from-[var(--brand)]/85 via-[#9333ea]/85 to-[var(--accent)]/85"
      >
        <div class="absolute inset-0 opacity-30 mix-blend-overlay"
          style="background-image: radial-gradient(circle at 25% 30%, white 0%, transparent 55%), radial-gradient(circle at 80% 70%, rgb(255,255,255,0.6) 0%, transparent 55%);">
        </div>
        <div class="absolute inset-0 grid place-items-center">
          <p class="font-display text-5xl font-bold text-white/90">
            {{ article.title?.charAt(0) || '·' }}
          </p>
        </div>
      </div>

      <!-- 顶部分类胶囊 -->
      <div class="absolute top-3 left-3 flex items-center gap-2">
        <span
          v-if="article.category"
          class="inline-flex items-center gap-1 rounded-full bg-black/45 backdrop-blur-md px-2.5 py-1 text-[11px] font-medium text-white"
        >
          <Folder class="size-3" />
          {{ article.category.name }}
        </span>
        <span
          v-if="article.is_featured"
          class="inline-flex items-center gap-1 rounded-full bg-amber-400/90 backdrop-blur-md px-2.5 py-1 text-[11px] font-semibold text-amber-950"
        >
          <Star class="size-3 fill-current" /> 精选
        </span>
      </div>
    </router-link>

    <!-- 内容区：占据 grid 第二行，min-h-0 防止 grid 行被内容撑大，overflow-hidden 兜底 -->
    <div class="flex min-h-0 w-full min-w-0 flex-col gap-3 overflow-hidden p-5 sm:p-6">
      <div class="flex shrink-0 items-center gap-3 overflow-hidden whitespace-nowrap text-[11px] text-[var(--text-muted)] tabular-nums">
        <span class="inline-flex shrink-0 items-center gap-1">
          <Calendar class="size-3" /> {{ formatFriendlyTime(article.created_at) }}
        </span>
        <span class="inline-flex shrink-0 items-center gap-1">
          <Eye class="size-3" /> {{ formatNumber(article.view_count ?? 0) }}
        </span>
        <span v-if="typeof article.comment_count === 'number'" class="inline-flex shrink-0 items-center gap-1">
          <MessageSquare class="size-3" /> {{ article.comment_count }}
        </span>
      </div>

      <h3 class="line-clamp-2 shrink-0 font-display text-xl font-semibold leading-snug tracking-tight text-[var(--text)] sm:text-[22px]">
        <router-link :to="`/article/${article.slug}`" class="link-underline">
          {{ article.title }}
        </router-link>
      </h3>

      <p class="line-clamp-3 flex-1 overflow-hidden text-[14px] leading-relaxed text-[var(--text-soft)]">
        {{ article.summary || '　' }}
      </p>

      <div class="flex shrink-0 items-center justify-between gap-3 overflow-hidden border-t border-[var(--border)] pt-3">
        <div class="flex min-w-0 flex-1 items-center gap-1.5 overflow-hidden whitespace-nowrap">
          <span
            v-for="tag in (article.tags ?? []).slice(0, 3)"
            :key="tag.id"
            class="max-w-[6rem] shrink-0 truncate rounded-md bg-[var(--bg-muted)] px-2 py-0.5 text-[11px] text-[var(--text-soft)]"
          >
            #{{ tag.name }}
          </span>
        </div>
        <router-link
          :to="`/article/${article.slug}`"
          class="inline-flex shrink-0 items-center gap-1 text-[13px] font-medium text-[var(--brand)] transition-all group-hover:gap-2"
        >
          阅读 <ArrowRight class="size-3.5" />
        </router-link>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { type Article } from '@/api/articles'
import { formatFriendlyTime } from '@/utils/time'
import { Calendar, Eye, MessageSquare, Folder, Star, ArrowRight } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  article: Article
  variant?: 'default' | 'featured' | 'compact'
}>(), {
  variant: 'default',
})

// 优先使用后端生成的 16:9 缩略图（卡片体积小、构图统一），
// 老数据没有缩略图时回退到原 cover_image，保证向后兼容。
const coverThumb = computed(() => props.article.cover_image_thumb || props.article.cover_image || '')

const formatNumber = (n: number) => {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}
</script>

