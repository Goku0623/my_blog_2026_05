<template>
  <div class="space-y-6">
    <!-- 顶部欢迎/统计 -->
    <section>
      <div class="mb-6 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 class="text-2xl font-semibold text-[var(--text)]">欢迎回来，{{ adminName }} 👋</h1>
          <p class="text-sm text-[var(--text-muted)] mt-1">这里是站点的实时概览</p>
        </div>
        <div class="text-xs text-[var(--text-muted)]">最后更新：{{ formatDateTime(updatedAt) }}</div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <StatCard label="文章总数" :value="stats.total_articles" :icon="FileText" color="blue" />
        <StatCard label="总阅读量" :value="stats.total_views" :icon="Eye" color="green" />
        <StatCard label="评论总数" :value="stats.total_comments" :icon="MessageSquare" color="orange">
          <template #extra><UTag variant="success">即时发布</UTag></template>
        </StatCard>
      </div>
    </section>

    <!-- 图表 -->
    <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <UCard padding="md">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">近 30 天阅读量趋势</span>
            <UTag variant="brand">Views</UTag>
          </div>
        </template>
        <div class="h-72">
          <v-chart
            v-if="chartsReady"
            class="size-full"
            :option="viewTrendOption"
            :autoresize="{ throttle: 200 }"
          />
          <div v-else class="h-full p-4">
            <USkeleton class="h-full rounded-xl" />
          </div>
        </div>
      </UCard>

      <UCard padding="md">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">近 7 天评论量</span>
            <UTag variant="success">Comments</UTag>
          </div>
        </template>
        <div class="h-72">
          <v-chart
            v-if="chartsReady"
            class="size-full"
            :option="commentTrendOption"
            :autoresize="{ throttle: 200 }"
          />
          <div v-else class="h-full p-4">
            <USkeleton class="h-full rounded-xl" />
          </div>
        </div>
      </UCard>
    </section>

    <!-- 健康状态 + 最近评论 -->
    <section class="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <UCard padding="md" body-class="space-y-4">
        <template #header>
          <div class="flex items-center justify-between">
            <span class="font-semibold">服务健康状态</span>
            <UTag :variant="health.status === 'healthy' ? 'success' : 'danger'">
              {{ health.status === 'healthy' ? '健康' : '异常' }}
            </UTag>
          </div>
        </template>
        <div class="space-y-3 text-sm">
          <HealthRow label="数据库" :status="health.database" />
          <HealthRow label="Redis" :status="health.redis" />
          <HealthRow label="Celery" :status="health.celery" />
          <div class="flex justify-between text-[var(--text-soft)]">
            <span>运行时间</span><span class="text-[var(--text)] tabular-nums transform-gpu will-change-[contents]">{{ liveUptime || health.uptime }}</span>
          </div>
        </div>
      </UCard>

      <UCard padding="none" class="lg:col-span-2">
        <template #header>
          <div class="flex items-center justify-between px-5 py-3">
            <span class="font-semibold">最近评论</span>
            <router-link to="/admin/comments" class="text-sm text-[var(--brand)] hover:underline">查看全部 →</router-link>
          </div>
        </template>
        <div v-if="recentComments.length === 0" class="p-6">
          <UEmpty description="暂无评论" />
        </div>
        <ul v-else class="divide-y divide-[var(--border)]">
          <li
            v-for="c in recentComments"
            :key="c.id"
            class="px-5 py-3 flex gap-3 hover:bg-[var(--bg-muted)] transition-colors"
          >
            <UAvatar :src="c.guest_avatar || undefined" :name="c.guest_name" :size="36" />
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 text-sm">
                <span class="font-medium text-[var(--text)]">{{ c.guest_name }}</span>
                <span class="text-[var(--text-muted)] text-xs">{{ formatFriendlyTime(c.created_at) }}</span>
                <UTag variant="success">已发布</UTag>
              </div>
              <p class="text-sm text-[var(--text-soft)] line-clamp-2 mt-0.5">{{ c.content }}</p>
              <p class="text-xs text-[var(--text-muted)] mt-1 truncate">→ {{ c.article_title }}</p>
            </div>
          </li>
        </ul>
      </UCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import {
  getDashboardStats, getTrends, getSystemHealth, getRecentComments,
  type DashboardStats, type SystemHealth, type RecentComment,
} from '@/api/statistics'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime, formatFriendlyTime } from '@/utils/time'
import { FileText, Eye, MessageSquare } from 'lucide-vue-next'
import { UCard, UTag, UAvatar, UEmpty, USkeleton, toast } from '@/ui'
import StatCard from '../components/StatCard.vue'
import HealthRow from '../components/HealthRow.vue'

use([CanvasRenderer, LineChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const authStore = useAuthStore()
const adminName = computed(() => authStore.adminInfo?.username || 'Admin')

const stats = ref<DashboardStats>({
  total_articles: 0,
  total_comments: 0,
  total_views: 0,
  today_views: 0,
})

const health = ref<SystemHealth>({
  status: 'checking',
  database: 'checking',
  redis: 'checking',
  celery: 'checking',
  uptime: '-',
  started_at: null,
})

const recentComments = ref<RecentComment[]>([])
const updatedAt = ref<string>(new Date().toISOString())
const chartsReady = ref(false)
let idleTaskHandle: number | null = null

const viewTrendOption = ref<any>(makeLineOption([], '#9333ea'))
const commentTrendOption = ref<any>(makeBarOption([], '#10b981'))

const DASHBOARD_CACHE_KEY = 'admin_dashboard_cache_v1'
const DASHBOARD_CACHE_TTL_MS = 2 * 60 * 1000

interface DashboardCachePayload {
  timestamp: number
  stats: DashboardStats
  health: SystemHealth
  recentComments: RecentComment[]
  viewTrendOption: any
  commentTrendOption: any
  updatedAt: string
}

function makeLineOption(data: { date: string; value: number }[], color: string) {
  return {
    animation: false,
    tooltip: { trigger: 'axis' },
    grid: { left: 12, right: 12, top: 16, bottom: 6 },
    xAxis: { type: 'category', boundaryGap: false, data: data.map((d) => d.date), axisLine: { lineStyle: { color: 'var(--border)' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border)' } } },
    series: [
      {
        name: '阅读量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: { opacity: 0.15, color },
        lineStyle: { width: 2.5, color },
        itemStyle: { color },
        data: data.map((d) => d.value),
      },
    ],
  }
}

function makeBarOption(data: { date: string; value: number }[], color: string) {
  return {
    animation: false,
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 12, right: 12, top: 16, bottom: 6 },
    xAxis: { type: 'category', data: data.map((d) => d.date), axisLine: { lineStyle: { color: 'var(--border)' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: 'var(--border)' } } },
    series: [
      {
        name: '评论数',
        type: 'bar',
        barWidth: '40%',
        itemStyle: { color, borderRadius: [6, 6, 0, 0] },
        data: data.map((d) => d.value),
      },
    ],
  }
}

const fetchData = async () => {
  const results = await Promise.allSettled([
    getDashboardStats(),
    getSystemHealth(),
    getRecentComments(5),
  ])

  let hasError = false
  const [statsRes, healthRes, commentsRes] = results

  if (statsRes.status === 'fulfilled') {
    stats.value = statsRes.value.data?.data ?? stats.value
  } else {
    hasError = true
  }

  if (healthRes.status === 'fulfilled') {
    health.value = healthRes.value.data?.data ?? health.value
  } else {
    hasError = true
  }

  if (commentsRes.status === 'fulfilled') {
    recentComments.value = commentsRes.value.data?.data ?? []
  } else {
    hasError = true
  }

  updatedAt.value = new Date().toISOString()
  if (hasError) {
    toast.warning('部分仪表盘数据暂不可用，已使用默认值展示')
  }
}

const fetchTrendData = async () => {
  const results = await Promise.allSettled([
    getTrends('views', 'month'),
    getTrends('comments', 'week'),
  ])

  let hasError = false
  const [viewsRes, commentsTrendRes] = results

  if (viewsRes.status === 'fulfilled') {
    viewTrendOption.value = makeLineOption(viewsRes.value.data?.data?.data ?? [], '#9333ea')
  } else {
    hasError = true
  }

  if (commentsTrendRes.status === 'fulfilled') {
    commentTrendOption.value = makeBarOption(commentsTrendRes.value.data?.data?.data ?? [], '#10b981')
  } else {
    hasError = true
  }

  chartsReady.value = true
  if (hasError) {
    toast.warning('部分趋势数据暂不可用，已降级展示')
  }
}

const readDashboardCache = (): DashboardCachePayload | null => {
  try {
    const raw = sessionStorage.getItem(DASHBOARD_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as DashboardCachePayload
    if (!parsed || typeof parsed.timestamp !== 'number') return null
    if (Date.now() - parsed.timestamp > DASHBOARD_CACHE_TTL_MS) return null
    return parsed
  } catch {
    return null
  }
}

const writeDashboardCache = () => {
  const payload: DashboardCachePayload = {
    timestamp: Date.now(),
    stats: stats.value,
    health: health.value,
    recentComments: recentComments.value,
    viewTrendOption: viewTrendOption.value,
    commentTrendOption: commentTrendOption.value,
    updatedAt: updatedAt.value,
  }
  try {
    sessionStorage.setItem(DASHBOARD_CACHE_KEY, JSON.stringify(payload))
  } catch {
  }
}

const scheduleTrendFetch = () => {
  const run = async () => {
    await fetchTrendData()
    writeDashboardCache()
  }
  const ric = window.requestIdleCallback
  if (typeof ric === 'function') {
    idleTaskHandle = ric(() => { void run() }, { timeout: 1200 })
    return
  }
  idleTaskHandle = window.setTimeout(() => { void run() }, 150)
}

const initDashboard = async () => {
  const cache = readDashboardCache()
  if (cache) {
    stats.value = cache.stats
    health.value = cache.health
    recentComments.value = cache.recentComments
    viewTrendOption.value = cache.viewTrendOption
    commentTrendOption.value = cache.commentTrendOption
    updatedAt.value = cache.updatedAt
    chartsReady.value = true
  }

  await fetchData()
  writeDashboardCache()
  if (cache) {
    scheduleTrendFetch()
  } else {
    await fetchTrendData()
    writeDashboardCache()
  }
}

onMounted(initDashboard)

const handleAdminProfileUpdated = () => {
  chartsReady.value = false
  void initDashboard()
}

onMounted(() => {
  window.addEventListener('admin-profile-updated', handleAdminProfileUpdated)
})

onBeforeUnmount(() => {
  window.removeEventListener('admin-profile-updated', handleAdminProfileUpdated)
  if (idleTaskHandle !== null) {
    const cic = window.cancelIdleCallback
    if (typeof cic === 'function') {
      cic(idleTaskHandle)
    } else {
      window.clearTimeout(idleTaskHandle)
    }
    idleTaskHandle = null
  }
  if (uptimeTimer !== null) {
    clearInterval(uptimeTimer)
    uptimeTimer = null
  }
})

const liveUptime = ref('')
let uptimeTimer: ReturnType<typeof setInterval> | null = null

const formatUptime = (totalSeconds: number) => {
  const s = Math.max(0, Math.floor(totalSeconds))
  const days = Math.floor(s / 86400)
  const hours = Math.floor((s % 86400) / 3600)
  const minutes = Math.floor((s % 3600) / 60)
  const sec = s % 60
  return `${days}d ${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
}

const startUptimeTimer = () => {
  if (uptimeTimer !== null) return
  const raw = health.value.started_at
  if (!raw) return
  const d = new Date(raw)
  if (isNaN(d.getTime())) return
  const startedMs = d.getTime()
  liveUptime.value = formatUptime((Date.now() - startedMs) / 1000)
  uptimeTimer = setInterval(() => {
    liveUptime.value = formatUptime((Date.now() - startedMs) / 1000)
  }, 1000)
}

const stopUptimeTimer = () => {
  if (uptimeTimer !== null) {
    clearInterval(uptimeTimer)
    uptimeTimer = null
  }
}

watch(() => health.value.started_at, (v) => {
  stopUptimeTimer()
  if (v) startUptimeTimer()
})
</script>
