<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <!-- 阅读进度条 -->
    <div class="reading-progress" aria-hidden="true">
      <i :style="{ '--progress': progressPercent + '%' }"></i>
    </div>

    <SiteNavbar />

    <!-- 加载中 -->
    <div v-if="loading" class="container-page py-16">
      <USkeleton height="60px" class="rounded-xl mb-6 max-w-3xl" />
      <USkeleton height="320px" class="rounded-2xl" />
    </div>

    <!-- 详情 -->
    <article v-else-if="article" class="flex-1 animate-fade-in">
      <!-- ============================================================
           Article Hero
           ============================================================ -->
      <header class="relative overflow-hidden">
        <div aria-hidden="true" class="hero-orb size-[480px] -top-40 -left-32 bg-[var(--brand)]/20"></div>
        <div aria-hidden="true" class="hero-orb size-[360px] top-0 right-[-100px] bg-[var(--accent)]/20"></div>

        <div class="container-page relative pt-10 sm:pt-14 lg:pt-16 pb-10 sm:pb-12">
          <div class="max-w-3xl">
            <div class="flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)] mb-5">
              <router-link
                v-if="article.category"
                :to="`/category/${article.category.id}`"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--brand-soft)] text-[var(--brand)] font-medium hover:opacity-80 transition-opacity"
              >
                <Folder class="size-3" />
                {{ article.category.name }}
              </router-link>
              <span class="inline-flex items-center gap-1.5">
                <Calendar class="size-3" /> {{ formatFriendlyTime(displayPublishedTime) }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Eye class="size-3" /> {{ article.view_count }} 阅读
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Clock class="size-3" /> {{ readingTime }} 分钟阅读
              </span>
            </div>

            <h1 class="hero-headline text-[clamp(2rem,5vw,4rem)] leading-[1.1] text-[var(--text)]">
              {{ article.title }}
            </h1>

            <p
              v-if="article.summary"
              class="mt-6 text-base sm:text-lg leading-relaxed text-[var(--text-soft)] border-l-2 border-[var(--brand)]/60 pl-4"
            >
              {{ article.summary }}
            </p>

            <div class="mt-8 flex items-center gap-4">
              <div class="grid place-items-center size-11 rounded-full bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] text-white font-semibold shadow-[var(--shadow-md)] overflow-hidden">
                <img v-if="siteStore.config.admin_avatar" :src="siteStore.config.admin_avatar" alt="" class="size-full object-cover" />
                <span v-else>{{ authorInitial }}</span>
              </div>
              <div>
                <p class="text-sm font-medium text-[var(--text)]">{{ siteStore.config.site_author || '作者' }}</p>
                <p class="text-xs text-[var(--text-muted)]">{{ siteStore.config.site_name }}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ============================================================
           Body：正文 + 侧栏
           ============================================================ -->
      <div class="container-page pb-16">
        <div class="grid gap-10 xl:grid-cols-[minmax(0,1fr)_260px] xl:gap-14">
          <!-- 正文 -->
          <div ref="articleBody" class="min-w-0">
            <div
              ref="articleContent"
              class="prose prose-slate max-w-none dark:prose-invert prose-pre:rounded-xl prose-img:rounded-xl prose-headings:scroll-mt-24"
              v-html="renderedContent"
            />

            <!-- 标签条 -->
            <div
              v-if="article.tags && article.tags.length > 0"
              class="mt-10 flex flex-wrap items-center gap-2 pt-6 border-t border-[var(--border)]"
            >
              <Hash class="size-4 text-[var(--text-muted)]" />
              <router-link
                v-for="tag in article.tags"
                :key="tag.id"
                :to="`/tag/${tag.id}`"
                class="inline-flex items-center px-2.5 py-1 text-xs rounded-md border border-[var(--border)] text-[var(--text-soft)] hover:border-[var(--brand)] hover:text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
              >
                #{{ tag.name }}
              </router-link>
            </div>

            <!-- 作者卡片 -->
            <div class="mt-12 relative overflow-hidden rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--brand-soft)]/60 via-[var(--surface)] to-[var(--surface)] p-6 sm:p-8">
              <div aria-hidden="true" class="absolute -top-12 -right-12 size-40 bg-[var(--brand)]/15 rounded-full blur-3xl"></div>
              <div class="relative flex flex-col sm:flex-row sm:items-center gap-5">
                <div class="grid place-items-center size-16 shrink-0 rounded-2xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white text-xl font-bold shadow-[var(--shadow-md)] overflow-hidden">
                  <img v-if="siteStore.config.admin_avatar" :src="siteStore.config.admin_avatar" alt="" class="size-full object-cover" />
                  <span v-else>{{ authorInitial }}</span>
                </div>
                <div class="flex-1 min-w-0">
                  <p class="eyebrow">Author</p>
                  <h3 class="mt-1 font-display text-xl font-semibold text-[var(--text)]">
                    {{ siteStore.config.site_author || siteStore.config.site_name }}
                  </h3>
                  <p class="mt-1 text-sm leading-relaxed text-[var(--text-soft)]">
                    {{ siteStore.config.site_description || '感谢阅读，欢迎交流！' }}
                  </p>
                </div>
                <router-link
                  to="/"
                  class="inline-flex items-center gap-1 self-start sm:self-center px-4 py-2 rounded-full text-sm font-medium text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
                >
                  更多文章 <ArrowRight class="size-3.5" />
                </router-link>
              </div>
            </div>

            <!-- 评论 -->
            <div class="mt-12">
              <div ref="commentTrigger" class="h-px w-full" aria-hidden="true"></div>
              <CommentSection v-if="canComment && shouldRenderComment" :article-id="article.id" />
              <div
                v-else-if="canComment"
                class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6"
              >
                <USkeleton height="20px" class="max-w-36 mb-4" />
                <USkeleton height="14px" class="mb-2" />
                <USkeleton height="14px" class="w-2/3" />
              </div>
              <div
                v-else
                class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-center text-sm text-[var(--text-soft)]"
              >
                评论功能已关闭
              </div>
            </div>
          </div>

          <!-- 侧栏（TOC + 信息） -->
          <aside class="hidden xl:block">
            <div class="sticky top-24 space-y-6">
              <!-- 目录 -->
              <div v-if="toc.length > 0" class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
                <p class="eyebrow mb-3">Contents</p>
                <ul class="space-y-1.5 text-sm">
                  <li v-for="item in toc" :key="item.id">
                    <a
                      :href="`#${item.id}`"
                      :class="[
                        'block leading-snug transition-colors py-1 border-l-2 pl-3',
                        activeHeading === item.id
                          ? 'border-[var(--brand)] text-[var(--brand)] font-medium'
                          : 'border-transparent text-[var(--text-soft)] hover:text-[var(--text)] hover:border-[var(--border-strong)]',
                      ]"
                      :style="{ marginLeft: `${(item.level - 1) * 8}px` }"
                      @click="onTocClick($event, item.id)"
                    >
                      {{ item.text }}
                    </a>
                  </li>
                </ul>
              </div>

              <!-- 文章信息 -->
              <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
                <p class="eyebrow mb-3">Info</p>
                <div class="space-y-3 text-sm">
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">发布</span>
                    <span class="text-[var(--text)] tabular-nums">{{ formatFriendlyTime(displayPublishedTime) }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">阅读量</span>
                    <span class="text-[var(--text)] tabular-nums">{{ article.view_count }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">字数</span>
                    <span class="text-[var(--text)] tabular-nums">{{ wordCount }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">阅读时长</span>
                    <span class="text-[var(--text)] tabular-nums">{{ readingTime }} 分钟</span>
                  </div>
                </div>
              </div>

              <!-- 回到顶部 -->
              <button
                class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-sm font-medium text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click="scrollTop"
              >
                <ArrowUp class="size-4" /> 回到顶部
              </button>
            </div>
          </aside>
        </div>
      </div>
    </article>

    <!-- 不存在 -->
    <div v-else class="container-page py-20">
      <UEmpty description="文章不存在或已被删除" />
    </div>

    <!-- 正文图片预览 Lightbox：v-show 避免重复创建 DOM -->
    <div
      v-show="lightboxVisible"
      :aria-hidden="!lightboxVisible"
      class="fixed inset-0 z-[120] bg-black/90"
      role="dialog"
      aria-modal="true"
      aria-label="图片预览"
      @click.self="closeLightbox"
      @wheel.prevent="onLightboxWheel"
    >
      <!-- 上一张 -->
      <button
        v-if="lightboxImages.length > 1"
        type="button"
        class="absolute left-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white/15 px-3 py-2 text-sm text-white hover:bg-white/25 transition-colors"
        @click="showPrevLightboxImage"
      >
        上一张
      </button>

      <!-- 下一张 -->
      <button
        v-if="lightboxImages.length > 1"
        type="button"
        class="absolute right-3 top-1/2 z-10 -translate-y-1/2 rounded-full bg-white/15 px-3 py-2 text-sm text-white hover:bg-white/25 transition-colors"
        @click="showNextLightboxImage"
      >
        下一张
      </button>

      <!-- 图片区域 -->
      <div
        class="flex h-full w-full items-center justify-center overflow-hidden p-12 sm:p-16"
        @click="closeLightbox"
      >
        <img
          ref="lightboxImg"
          :src="lightboxImageSrc"
          :alt="lightboxImageAlt"
          class="max-h-full max-w-full rounded-xl object-contain shadow-2xl select-none"
          style="transform-origin: center center; will-change: transform; transform: translate3d(0,0,0) scale3d(1,1,1); transition: transform 0.15s linear; cursor: zoom-in; touch-action: none;"
          draggable="false"
          @click.stop
          @pointerdown="onLightboxImgPointerdown"
          @pointermove="onLightboxImgPointermove"
          @pointerup="onLightboxImgPointerup"
          @pointercancel="onLightboxImgPointerup"
          @dblclick="_lbZoom === 1 ? zoomIn() : resetLightboxZoom()"
        />
      </div>

      <!-- 底部工具栏：缩放控制 + 图片计数 -->
      <div class="absolute bottom-4 inset-x-0 z-10 flex items-center justify-center gap-3 px-4 pointer-events-none">
        <!-- 缩放控件：ref 由 _applyLbTransform 直接操作，无任何 Vue 响应式绑定 -->
        <div class="flex items-center gap-1 rounded-full bg-white/15 px-1.5 py-1 pointer-events-auto">
          <button
            ref="lbBtnZoomOut"
            type="button"
            class="grid place-items-center size-7 rounded-full text-white text-base font-medium transition-colors hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed"
            title="缩小 (-)"
            @click="zoomOut"
          >−</button>
          <button
            ref="lbZoomText"
            type="button"
            class="min-w-[3.2rem] text-center text-xs text-white/90 tabular-nums hover:text-white transition-colors px-1"
            title="重置缩放 (0)"
            @click="resetLightboxZoom"
          >100%</button>
          <button
            ref="lbBtnZoomIn"
            type="button"
            class="grid place-items-center size-7 rounded-full text-white text-base font-medium transition-colors hover:bg-white/20 disabled:opacity-30 disabled:cursor-not-allowed"
            title="放大 (+)"
            @click="zoomIn"
          >+</button>
        </div>

        <!-- 图片计数 -->
        <div
          v-if="lightboxImages.length > 1"
          class="rounded-full bg-white/15 px-3 py-1 text-xs text-white pointer-events-none"
        >
          {{ lightboxIndex + 1 }} / {{ lightboxImages.length }}
        </div>
      </div>
    </div>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick, useTemplateRef, defineAsyncComponent } from 'vue'
import { useRoute } from 'vue-router'
import { getArticle, type Article } from '@/api/articles'
import { useMarkdown } from '@/composables/useMarkdown'
import { useSiteStore } from '@/stores/site'
import { formatFriendlyTime } from '@/utils/time'
import { ArrowUp, ArrowRight, Calendar, Eye, Folder, Hash, Clock } from 'lucide-vue-next'
import { UEmpty, USkeleton, toast } from '@/ui'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const route = useRoute()
const { render } = useMarkdown()
const siteStore = useSiteStore()

const article = ref<Article | null>(null)
const loading = ref(true)
const articleBody = useTemplateRef<HTMLElement>('articleBody')
const articleContent = useTemplateRef<HTMLElement>('articleContent')
const commentTrigger = useTemplateRef<HTMLElement>('commentTrigger')
const shouldRenderComment = ref(false)
let commentObserver: IntersectionObserver | null = null
const CommentSection = defineAsyncComponent(() => import('../components/CommentSection.vue'))

interface TocItem {
  id: string
  text: string
  level: number
}
interface HeadingPosition {
  id: string
  top: number
}
const toc = ref<TocItem[]>([])
const headingPositions = ref<HeadingPosition[]>([])
const activeHeading = ref('')
const progressPercent = ref(0)
let scrollRafId: number | null = null
let articleImageLoadAbortController: AbortController | null = null
let articleImagePreviewAbortController: AbortController | null = null
let resizeDebounceTimer: number | null = null
const lightboxImages = ref<Array<{ src: string; alt: string }>>([])
const lightboxVisible = ref(false)
const lightboxImageSrc = ref('')
const lightboxImageAlt = ref('')
const lightboxIndex = ref(0)
const lightboxImgEl = useTemplateRef<HTMLImageElement>('lightboxImg')
const lbZoomTextEl = useTemplateRef<HTMLElement>('lbZoomText')
const lbBtnZoomIn = useTemplateRef<HTMLButtonElement>('lbBtnZoomIn')
const lbBtnZoomOut = useTemplateRef<HTMLButtonElement>('lbBtnZoomOut')
let _lbZoom = 1
let _lbPanX = 0
let _lbPanY = 0
let _lbDragging = false
let _lbDragOX = 0
let _lbDragOY = 0
let _lbDragOPX = 0
let _lbDragOPY = 0
let _lbLastMoveTs = 0
let _lbLastPanX = 0
let _lbLastPanY = 0
let _lbVelocityX = 0
let _lbVelocityY = 0
let _lbTransitionTimer: number | null = null
let _lbApplyRaf: number | null = null
let _lbInertiaRaf: number | null = null
let _lbInertiaLastTs = 0
let _lbPreloadTimer: number | null = null
const _lbPointers = new Map<number, { x: number; y: number }>()
let _lbPinching = false
let _lbPinchDist = 0
let _lbPinchZoom = 1
let _lbPinchMidX = 0
let _lbPinchMidY = 0
const ZOOM_MIN = 0.25
const ZOOM_MAX = 5
const ZOOM_STEP = 0.12
const PRELOAD_OFFSETS = [0, 1, -1, 2, -2, 3, -3]
const MAX_PRELOAD_CACHE_SIZE = 240
const lightboxPreloadCache = new Set<string>()

const renderedContent = computed(() => {
  if (!article.value) return ''
  if (article.value.content) return render(article.value.content)
  return article.value.rendered_content || ''
})

const canComment = computed(() => {
  if (!siteStore.config.comment_enabled) return false
  if (!article.value) return false
  return article.value.allow_comment !== false
})

const wordCount = computed(() => {
  const html = renderedContent.value
  if (!html) return 0

  const container = document.createElement('div')
  container.innerHTML = html
  container.querySelectorAll('script, style, noscript').forEach((el) => el.remove())
  const plainText = container.textContent || ''
  return plainText.replace(/\s+/g, '').length
})

const readingTime = computed(() => Math.max(1, Math.round(wordCount.value / 350)))
const displayPublishedTime = computed(() => article.value?.published_at || article.value?.created_at || '')

const authorInitial = computed(() => {
  const name = siteStore.config.site_author || siteStore.config.site_name || 'A'
  return Array.from(name)[0]?.toUpperCase() ?? 'A'
})

const fetchArticle = async () => {
  loading.value = true
  try {
    const slug = route.params.slug as string
    const res = await getArticle(slug)
    article.value = res.data?.data ?? null
    if (article.value) {
      document.title = `${article.value.title} - ${article.value.category?.name ?? '博客'}`
      shouldRenderComment.value = false
    }
  } catch (e) {
    console.error(e)
    toast.error('获取文章详情失败')
  } finally {
    loading.value = false
  }
  if (article.value) {
    await nextTick()
    buildToc()
    bindBodyImageLoadListener()
    setupCommentObserver()
  }
}

const buildToc = () => {
  if (!articleBody.value) {
    toc.value = []
    headingPositions.value = []
    activeHeading.value = ''
    return
  }
  const headings = articleBody.value.querySelectorAll('h2, h3, h4')
  const items: TocItem[] = []
  const positions: HeadingPosition[] = []
  headings.forEach((h, i) => {
    const el = h as HTMLElement
    if (!el.id) el.id = `heading-${i}`
    const level = Number(el.tagName.replace('H', '')) - 1
    items.push({
      id: el.id,
      text: el.innerText || el.textContent || '',
      level,
    })
    positions.push({
      id: el.id,
      top: window.scrollY + el.getBoundingClientRect().top,
    })
  })
  toc.value = items
  headingPositions.value = positions
}

const bindBodyImageLoadListener = () => {
  articleImageLoadAbortController?.abort()
  articleImagePreviewAbortController?.abort()
  if (!articleContent.value) return
  const loadController = new AbortController()
  const previewController = new AbortController()
  articleImageLoadAbortController = loadController
  articleImagePreviewAbortController = previewController

  const images = articleContent.value.querySelectorAll<HTMLImageElement>('img')
  const imageItems: Array<{ src: string; alt: string }> = []
  images.forEach((img) => {
    const src = resolvePreviewSrc(img)
    if (!src) {
      delete img.dataset.lightboxIndex
      img.classList.remove('article-previewable-image')
      return
    }
    img.dataset.lightboxIndex = String(imageItems.length)
    img.classList.add('article-previewable-image')
    imageItems.push({
      src,
      alt: img.alt || '',
    })
    if (src !== img.src) {
      img.src = src
    }

    const shell = decoratePreviewableImage(img)
    const currentIndex = Number(img.dataset.lightboxIndex ?? '-1')
    if (currentIndex >= 0) {
      shell.addEventListener('click', (event) => {
        event.preventDefault()
        event.stopPropagation()
        openLightbox(currentIndex)
      }, { signal: previewController.signal })
      shell.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' && event.key !== ' ') return
        event.preventDefault()
        openLightbox(currentIndex)
      }, { signal: previewController.signal })
    }
  })
  lightboxImages.value = imageItems

  images.forEach((img) => {
    if (!img.complete) {
      img.addEventListener('load', handleResize, { signal: loadController.signal })
      img.addEventListener('error', handleResize, { signal: loadController.signal })
    }
  })
}

const decodeImageSrc = (src: string): string => {
  if (!src) return ''
  const value = src.trim()
  if (!value) return ''
  return value.replace(/&amp;/gi, '&')
}

const resolvePreviewSrc = (img: HTMLImageElement): string => {
  const candidates = [
    img.getAttribute('data-src'),
    img.getAttribute('data-original'),
    img.currentSrc,
    img.src,
    img.getAttribute('src'),
  ]
  for (const candidate of candidates) {
    const decoded = decodeImageSrc(candidate || '')
    if (decoded) return decoded
  }
  return ''
}

const decoratePreviewableImage = (img: HTMLImageElement): HTMLElement => {
  const currentParent = img.parentElement
  let shell: HTMLElement
  if (currentParent?.classList.contains('article-image-preview-shell')) {
    shell = currentParent
  } else {
    shell = document.createElement('span')
    shell.className = 'article-image-preview-shell'
    img.replaceWith(shell)
    shell.appendChild(img)
    const hint = document.createElement('span')
    hint.className = 'article-image-preview-hint'
    hint.textContent = '点击预览'
    shell.appendChild(hint)
  }

  shell.setAttribute('role', 'button')
  shell.setAttribute('tabindex', '0')
  shell.setAttribute('aria-label', '预览图片')
  shell.setAttribute('title', '点击预览图片')
  return shell
}

const _setLbTransition = (enabled: boolean) => {
  const img = lightboxImgEl.value
  if (!img) return
  img.style.transition = enabled ? 'transform 0.15s linear' : 'none'
}

const _clampLbPan = () => {
  const img = lightboxImgEl.value
  if (!img || _lbZoom <= 1) {
    _lbPanX = 0
    _lbPanY = 0
    return { clampedX: false, clampedY: false }
  }
  const baseWidth = Math.max(1, img.offsetWidth)
  const baseHeight = Math.max(1, img.offsetHeight)
  const maxPanX = Math.max(0, (baseWidth * _lbZoom - baseWidth) / 2)
  const maxPanY = Math.max(0, (baseHeight * _lbZoom - baseHeight) / 2)
  const prevPanX = _lbPanX
  const prevPanY = _lbPanY
  _lbPanX = Math.min(maxPanX, Math.max(-maxPanX, _lbPanX))
  _lbPanY = Math.min(maxPanY, Math.max(-maxPanY, _lbPanY))
  return {
    clampedX: _lbPanX !== prevPanX,
    clampedY: _lbPanY !== prevPanY,
  }
}

const _stopLbInertia = () => {
  if (_lbInertiaRaf !== null) {
    window.cancelAnimationFrame(_lbInertiaRaf)
    _lbInertiaRaf = null
  }
}

const _startLbInertia = () => {
  _stopLbInertia()
  if (_lbZoom <= 1) return
  const minSpeed = 0.01
  if (Math.abs(_lbVelocityX) < minSpeed && Math.abs(_lbVelocityY) < minSpeed) return
  _setLbTransition(false)
  _lbInertiaLastTs = performance.now()

  const tick = (now: number) => {
    const dt = Math.max(1, now - _lbInertiaLastTs)
    _lbInertiaLastTs = now
    const friction = Math.pow(0.92, dt / 16.67)
    _lbVelocityX *= friction
    _lbVelocityY *= friction
    _lbPanX += _lbVelocityX * dt
    _lbPanY += _lbVelocityY * dt
    const clamped = _clampLbPan()
    if (clamped.clampedX) _lbVelocityX = 0
    if (clamped.clampedY) _lbVelocityY = 0
    _applyLbTransformNow()

    if (Math.abs(_lbVelocityX) < minSpeed && Math.abs(_lbVelocityY) < minSpeed) {
      _lbInertiaRaf = null
      _setLbTransition(true)
      return
    }
    _lbInertiaRaf = window.requestAnimationFrame(tick)
  }

  _lbInertiaRaf = window.requestAnimationFrame(tick)
}

const _preloadLightboxImage = (src: string) => {
  if (!src || lightboxPreloadCache.has(src)) return
  lightboxPreloadCache.add(src)
  if (lightboxPreloadCache.size > MAX_PRELOAD_CACHE_SIZE) {
    lightboxPreloadCache.clear()
    lightboxPreloadCache.add(src)
  }
  const img = new Image()
  img.decoding = 'async'
  img.src = src
}

const _scheduleLightboxPreload = (centerIndex: number) => {
  if (_lbPreloadTimer !== null) {
    window.clearTimeout(_lbPreloadTimer)
    _lbPreloadTimer = null
  }
  _lbPreloadTimer = window.setTimeout(() => {
    _lbPreloadTimer = null
    const total = lightboxImages.value.length
    if (!total) return
    for (const offset of PRELOAD_OFFSETS) {
      const idx = (centerIndex + offset + total) % total
      const src = lightboxImages.value[idx]?.src || ''
      _preloadLightboxImage(src)
    }
  }, 16)
}

const _getFirstTwoPointers = () => {
  const iterator = _lbPointers.values()
  const first = iterator.next().value as { x: number; y: number } | undefined
  const second = iterator.next().value as { x: number; y: number } | undefined
  if (!first || !second) return null
  return [first, second] as const
}

const _resetLbGestureState = () => {
  _lbPointers.clear()
  _lbPinching = false
  _lbDragging = false
  _lbVelocityX = 0
  _lbVelocityY = 0
}

const _applyLbTransformNow = () => {
  const img = lightboxImgEl.value
  if (!img) return
  _clampLbPan()
  img.style.transform = `translate3d(${_lbPanX}px,${_lbPanY}px,0) scale3d(${_lbZoom},${_lbZoom},1)`
  img.style.cursor = _lbZoom > 1 ? ((_lbDragging || _lbPinching) ? 'grabbing' : 'grab') : 'zoom-in'
  if (lbZoomTextEl.value) lbZoomTextEl.value.textContent = `${Math.round(_lbZoom * 100)}%`
  if (lbBtnZoomOut.value) lbBtnZoomOut.value.disabled = _lbZoom <= ZOOM_MIN
  if (lbBtnZoomIn.value) lbBtnZoomIn.value.disabled = _lbZoom >= ZOOM_MAX
}

const _scheduleLbTransform = () => {
  if (_lbApplyRaf !== null) return
  _lbApplyRaf = window.requestAnimationFrame(() => {
    _lbApplyRaf = null
    _applyLbTransformNow()
  })
}

const _zoomAroundPoint = (nextZoom: number, clientX: number, clientY: number) => {
  const img = lightboxImgEl.value
  const prevZoom = _lbZoom
  if (!img || nextZoom === prevZoom) {
    _lbZoom = nextZoom
    return
  }
  const rect = img.getBoundingClientRect()
  const dx = clientX - (rect.left + rect.width / 2)
  const dy = clientY - (rect.top + rect.height / 2)
  const ratio = nextZoom / prevZoom
  _lbPanX = _lbPanX * ratio + dx * (1 - ratio)
  _lbPanY = _lbPanY * ratio + dy * (1 - ratio)
  _lbZoom = nextZoom
}

const _suppressLbTransition = () => {
  if (_lbTransitionTimer !== null) {
    window.clearTimeout(_lbTransitionTimer)
    _lbTransitionTimer = null
  }
  _setLbTransition(false)
  _lbTransitionTimer = window.setTimeout(() => {
    _lbTransitionTimer = null
    _setLbTransition(true)
  }, 180)
}

const _ensureLbTransition = () => {
  if (_lbTransitionTimer !== null) {
    window.clearTimeout(_lbTransitionTimer)
    _lbTransitionTimer = null
  }
  _setLbTransition(true)
}

const resetLightboxZoom = () => {
  _stopLbInertia()
  if (_lbTransitionTimer !== null) {
    window.clearTimeout(_lbTransitionTimer)
    _lbTransitionTimer = null
  }
  _resetLbGestureState()
  _lbZoom = 1
  _lbPanX = 0
  _lbPanY = 0
  _setLbTransition(true)
  _scheduleLbTransform()
}

const syncLightboxImageByIndex = () => {
  const item = lightboxImages.value[lightboxIndex.value]
  if (!item) return
  lightboxImageSrc.value = item.src
  lightboxImageAlt.value = item.alt
  _preloadLightboxImage(item.src)
  _scheduleLightboxPreload(lightboxIndex.value)
  resetLightboxZoom()
}

const openLightbox = (index: number) => {
  if (!lightboxImages.value.length) return
  const safeIndex = Math.max(0, Math.min(index, lightboxImages.value.length - 1))
  lightboxIndex.value = safeIndex
  syncLightboxImageByIndex()
  lightboxVisible.value = true
}

const closeLightbox = () => {
  lightboxVisible.value = false
  resetLightboxZoom()
}

const zoomIn = () => {
  _ensureLbTransition()
  _zoomAroundPoint(
    Math.min(ZOOM_MAX, _lbZoom + ZOOM_STEP),
    window.innerWidth / 2,
    window.innerHeight / 2,
  )
  _scheduleLbTransform()
}

const zoomOut = () => {
  _ensureLbTransition()
  _zoomAroundPoint(
    Math.max(ZOOM_MIN, _lbZoom - ZOOM_STEP),
    window.innerWidth / 2,
    window.innerHeight / 2,
  )
  _scheduleLbTransform()
}

const onLightboxWheel = (event: WheelEvent) => {
  event.preventDefault()
  _stopLbInertia()
  _suppressLbTransition()
  const scaleFactor = Math.exp(-event.deltaY * 0.0015)
  const nextZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, _lbZoom * scaleFactor))
  _zoomAroundPoint(nextZoom, event.clientX, event.clientY)
  _lbVelocityX = 0
  _lbVelocityY = 0
  _scheduleLbTransform()
}

const onLightboxImgPointerdown = (event: PointerEvent) => {
  _stopLbInertia()
  const target = event.currentTarget as HTMLElement
  target.setPointerCapture(event.pointerId)
  _lbPointers.set(event.pointerId, { x: event.clientX, y: event.clientY })
  if (_lbPointers.size >= 2) {
    const points = _getFirstTwoPointers()
    if (!points) return
    const [p1, p2] = points
    _lbPinching = true
    _lbDragging = false
    _lbPinchDist = Math.hypot(p2.x - p1.x, p2.y - p1.y) || 1
    _lbPinchZoom = _lbZoom
    _lbPinchMidX = (p1.x + p2.x) / 2
    _lbPinchMidY = (p1.y + p2.y) / 2
    _setLbTransition(false)
    _scheduleLbTransform()
    return
  }
  if (_lbZoom <= 1) return
  event.preventDefault()
  _lbDragging = true
  _lbDragOX = event.clientX
  _lbDragOY = event.clientY
  _lbDragOPX = _lbPanX
  _lbDragOPY = _lbPanY
  _lbLastPanX = _lbPanX
  _lbLastPanY = _lbPanY
  _lbLastMoveTs = performance.now()
  _lbVelocityX = 0
  _lbVelocityY = 0
  _setLbTransition(false)
  _scheduleLbTransform()
}

const onLightboxImgPointermove = (event: PointerEvent) => {
  if (_lbPointers.has(event.pointerId)) {
    _lbPointers.set(event.pointerId, { x: event.clientX, y: event.clientY })
  }
  if (_lbPinching && _lbPointers.size >= 2) {
    event.preventDefault()
    const points = _getFirstTwoPointers()
    if (!points) return
    const [p1, p2] = points
    const dist = Math.hypot(p2.x - p1.x, p2.y - p1.y) || _lbPinchDist
    const midX = (p1.x + p2.x) / 2
    const midY = (p1.y + p2.y) / 2
    const nextZoom = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, _lbPinchZoom * (dist / _lbPinchDist)))
    _zoomAroundPoint(nextZoom, midX, midY)
    _lbPanX += midX - _lbPinchMidX
    _lbPanY += midY - _lbPinchMidY
    _lbPinchDist = dist
    _lbPinchZoom = _lbZoom
    _lbPinchMidX = midX
    _lbPinchMidY = midY
    _scheduleLbTransform()
    return
  }
  if (!_lbDragging) return
  _lbPanX = _lbDragOPX + (event.clientX - _lbDragOX)
  _lbPanY = _lbDragOPY + (event.clientY - _lbDragOY)
  const now = performance.now()
  const dt = Math.max(1, now - _lbLastMoveTs)
  _lbVelocityX = (_lbPanX - _lbLastPanX) / dt
  _lbVelocityY = (_lbPanY - _lbLastPanY) / dt
  _lbLastPanX = _lbPanX
  _lbLastPanY = _lbPanY
  _lbLastMoveTs = now
  _scheduleLbTransform()
}

const onLightboxImgPointerup = (event: PointerEvent) => {
  const target = event.currentTarget as HTMLElement
  if (target.hasPointerCapture(event.pointerId)) {
    target.releasePointerCapture(event.pointerId)
  }
  _lbPointers.delete(event.pointerId)
  if (_lbPinching && _lbPointers.size >= 2) {
    _scheduleLbTransform()
    return
  }
  if (_lbPinching && _lbPointers.size < 2) {
    _lbPinching = false
    if (_lbPointers.size === 1 && _lbZoom > 1) {
      const onlyPointer = _lbPointers.values().next().value as { x: number; y: number }
      _lbDragging = true
      _lbDragOX = onlyPointer.x
      _lbDragOY = onlyPointer.y
      _lbDragOPX = _lbPanX
      _lbDragOPY = _lbPanY
      _lbLastPanX = _lbPanX
      _lbLastPanY = _lbPanY
      _lbLastMoveTs = performance.now()
      _lbVelocityX = 0
      _lbVelocityY = 0
      _setLbTransition(false)
      _scheduleLbTransform()
      return
    }
  }
  if (!_lbDragging) return
  _lbDragging = false
  if (_lbPointers.size > 0) {
    _scheduleLbTransform()
    return
  }
  _setLbTransition(true)
  _scheduleLbTransform()
  _startLbInertia()
}

const showPrevLightboxImage = () => {
  if (!lightboxImages.value.length) return
  const total = lightboxImages.value.length
  lightboxIndex.value = (lightboxIndex.value - 1 + total) % total
  syncLightboxImageByIndex()
}

const showNextLightboxImage = () => {
  if (!lightboxImages.value.length) return
  const total = lightboxImages.value.length
  lightboxIndex.value = (lightboxIndex.value + 1) % total
  syncLightboxImageByIndex()
}

const onWindowKeydown = (event: KeyboardEvent) => {
  if (!lightboxVisible.value) return
  if (event.key === 'Escape') {
    closeLightbox()
    return
  }
  if (event.key === 'ArrowLeft') {
    showPrevLightboxImage()
    return
  }
  if (event.key === 'ArrowRight') {
    showNextLightboxImage()
    return
  }
  if (event.key === '+' || event.key === '=') {
    zoomIn()
    return
  }
  if (event.key === '-') {
    zoomOut()
    return
  }
  if (event.key === '0') {
    resetLightboxZoom()
  }
}

const onTocClick = (e: MouseEvent, id: string) => {
  e.preventDefault()
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeHeading.value = id
  }
}

const updateScrollState = () => {
  const currentScrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  progressPercent.value = docHeight > 0 ? Math.min(100, (currentScrollTop / docHeight) * 100) : 0

  if (headingPositions.value.length === 0) {
    activeHeading.value = ''
    return
  }

  const offset = 120
  const currentY = currentScrollTop + offset
  let current = headingPositions.value[0].id
  for (const heading of headingPositions.value) {
    if (heading.top <= currentY) {
      current = heading.id
    } else {
      break
    }
  }
  activeHeading.value = current
}

const requestScrollStateUpdate = () => {
  if (scrollRafId !== null) return
  scrollRafId = window.requestAnimationFrame(() => {
    scrollRafId = null
    updateScrollState()
  })
}

const handleResize = () => {
  if (resizeDebounceTimer !== null) {
    window.clearTimeout(resizeDebounceTimer)
  }
  resizeDebounceTimer = window.setTimeout(() => {
    resizeDebounceTimer = null
    buildToc()
    requestScrollStateUpdate()
  }, 150)
}

const setupCommentObserver = () => {
  commentObserver?.disconnect()
  commentObserver = null
  if (!canComment.value) return

  const trigger = commentTrigger.value
  if (!trigger || !('IntersectionObserver' in window)) {
    shouldRenderComment.value = true
    return
  }

  commentObserver = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      shouldRenderComment.value = true
      commentObserver?.disconnect()
      commentObserver = null
    }
  }, { rootMargin: '360px 0px' })
  commentObserver.observe(trigger)
}

const scrollTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(
  () => route.params.slug,
  (newSlug) => {
    if (newSlug) fetchArticle()
  }
)

watch(renderedContent, async () => {
  await nextTick()
  closeLightbox()
  buildToc()
  bindBodyImageLoadListener()
  setupCommentObserver()
  requestScrollStateUpdate()
})

watch(canComment, async () => {
  await nextTick()
  setupCommentObserver()
})

onMounted(() => {
  fetchArticle()
  window.addEventListener('scroll', requestScrollStateUpdate, { passive: true })
  window.addEventListener('resize', handleResize, { passive: true })
  window.addEventListener('keydown', onWindowKeydown)
  requestScrollStateUpdate()
})

watch(lightboxVisible, (visible) => {
  document.body.style.overflow = visible ? 'hidden' : ''
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', requestScrollStateUpdate)
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('keydown', onWindowKeydown)
  articleImageLoadAbortController?.abort()
  articleImagePreviewAbortController?.abort()
  commentObserver?.disconnect()
  document.body.style.overflow = ''
  if (resizeDebounceTimer !== null) {
    window.clearTimeout(resizeDebounceTimer)
    resizeDebounceTimer = null
  }
  if (scrollRafId !== null) {
    window.cancelAnimationFrame(scrollRafId)
    scrollRafId = null
  }
  if (_lbTransitionTimer !== null) {
    window.clearTimeout(_lbTransitionTimer)
    _lbTransitionTimer = null
  }
  if (_lbApplyRaf !== null) {
    window.cancelAnimationFrame(_lbApplyRaf)
    _lbApplyRaf = null
  }
  _stopLbInertia()
  if (_lbPreloadTimer !== null) {
    window.clearTimeout(_lbPreloadTimer)
    _lbPreloadTimer = null
  }
})
</script>
