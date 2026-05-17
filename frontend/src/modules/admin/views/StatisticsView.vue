<template>
  <div class="space-y-4">
    <UCard padding="md">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-3">
          <span class="font-semibold">数据趋势分析</span>
          <div class="flex flex-wrap gap-2">
            <SegControl v-model="trendMetric" :items="metricItems" @change="scheduleTrendFetch" />
            <SegControl v-model="trendPeriod" :items="periodItems" @change="scheduleTrendFetch" />
          </div>
        </div>
      </template>
      <div class="h-80">
        <v-chart
          v-if="chartsReady"
          class="size-full"
          :option="trendOption"
          :autoresize="{ throttle: 200 }"
        />
        <div v-else class="h-full p-4">
          <USkeleton class="h-full rounded-xl" />
        </div>
      </div>
    </UCard>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <UCard padding="md">
        <template #header>
          <span class="font-semibold">接口调用 Top 10（24 小时）</span>
        </template>
        <div class="h-80">
          <v-chart
            v-if="chartsReady"
            class="size-full"
            :option="apiOption"
            :autoresize="{ throttle: 200 }"
          />
          <div v-else class="h-full p-4">
            <USkeleton class="h-full rounded-xl" />
          </div>
        </div>
      </UCard>

      <UCard padding="md">
        <template #header>
          <span class="font-semibold">文章分类分布</span>
        </template>
        <div class="h-80">
          <v-chart
            v-if="chartsReady"
            class="size-full"
            :option="categoryOption"
            :autoresize="{ throttle: 200 }"
          />
          <div v-else class="h-full p-4">
            <USkeleton class="h-full rounded-xl" />
          </div>
        </div>
      </UCard>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, h } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { getTrends, getApiMonitor, getCategoryStats } from '@/api/statistics'
import { UCard, USkeleton, toast } from '@/ui'

use([
  CanvasRenderer, LineChart, BarChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
])

const SegControl = (props: any, { emit }: any) =>
  h(
    'div',
    { class: 'inline-flex p-0.5 rounded-lg border border-[var(--border)] bg-[var(--bg-soft)]' },
    props.items.map((item: any) =>
      h(
        'button',
        {
          class: [
            'px-3 h-8 text-xs rounded-md transition-colors',
            props.modelValue === item.value
              ? 'bg-[var(--surface)] text-[var(--brand)] shadow-[var(--shadow-sm)] font-medium'
              : 'text-[var(--text-soft)] hover:text-[var(--text)]',
          ],
          onClick: () => {
            emit('update:modelValue', item.value)
            emit('change', item.value)
          },
        },
        item.label
      )
    )
  )
;(SegControl as any).props = ['modelValue', 'items']
;(SegControl as any).emits = ['update:modelValue', 'change']

const metricItems = [
  { label: '阅读量', value: 'views' },
  { label: '评论量', value: 'comments' },
  { label: '文章数', value: 'articles' },
  { label: '访客数', value: 'visitors' },
]
const periodItems = [
  { label: '按日', value: 'day' },
  { label: '按周', value: 'week' },
  { label: '按月', value: 'month' },
]

const trendMetric = ref<'views' | 'comments' | 'articles' | 'visitors'>('views')
const trendPeriod = ref<'day' | 'week' | 'month'>('day')

const trendOption = ref<any>({})
const apiOption = ref<any>({})
const categoryOption = ref<any>({})
const chartsReady = ref(false)
let trendDebounceTimer: number | null = null
let trendRequestSerial = 0
let otherRequestSerial = 0
let backgroundRefreshTimer: number | null = null

const STATS_CACHE_KEY = 'admin_statistics_cache_v1'
const STATS_CACHE_TTL_MS = 2 * 60 * 1000

interface StatisticsCachePayload {
  timestamp: number
  trendMetric: 'views' | 'comments' | 'articles' | 'visitors'
  trendPeriod: 'day' | 'week' | 'month'
  trendOption: any
  apiOption: any
  categoryOption: any
}

const fetchTrendData = async () => {
  const currentSerial = ++trendRequestSerial
  try {
    const res = await getTrends(trendMetric.value, trendPeriod.value)
    if (currentSerial !== trendRequestSerial) return
    const data = res.data?.data?.data ?? []
    const labelMap: Record<string, string> = {
      views: '阅读量', comments: '评论量', articles: '文章数', visitors: '访客数',
    }
    trendOption.value = {
      animation: false,
      tooltip: { trigger: 'axis' },
      grid: { left: 12, right: 16, top: 24, bottom: 8 },
      xAxis: { type: 'category', boundaryGap: false, data: data.map((i: any) => i.date) },
      yAxis: { type: 'value' },
      series: [{
        name: labelMap[trendMetric.value],
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: { opacity: 0.15, color: '#9333ea' },
        lineStyle: { width: 2.5, color: '#9333ea' },
        itemStyle: { color: '#9333ea' },
        data: data.map((i: any) => i.value),
      }],
    }
  } catch {
    toast.error('获取趋势数据失败')
  }
}

const scheduleTrendFetch = () => {
  if (trendDebounceTimer !== null) {
    window.clearTimeout(trendDebounceTimer)
  }
  trendDebounceTimer = window.setTimeout(async () => {
    trendDebounceTimer = null
    await fetchTrendData()
    writeStatisticsCache()
  }, 180)
}

const fetchOtherData = async () => {
  const currentSerial = ++otherRequestSerial
  const results = await Promise.allSettled([
    getApiMonitor(24),
    getCategoryStats(),
  ])
  if (currentSerial !== otherRequestSerial) return

  let hasError = false
  const [apiRes, catRes] = results

  if (apiRes.status === 'fulfilled') {
    const apiData = (apiRes.value.data?.data ?? []).slice(0, 10).reverse()
    apiOption.value = {
      animation: false,
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 12, right: 16, top: 16, bottom: 8 },
      xAxis: { type: 'value' },
      yAxis: { type: 'category', data: apiData.map((i: any) => i.endpoint) },
      series: [{
        name: '调用次数',
        type: 'bar',
        data: apiData.map((i: any) => i.total_calls),
        itemStyle: { color: '#3b82f6', borderRadius: [0, 4, 4, 0] },
      }],
    }
  } else {
    hasError = true
  }

  if (catRes.status === 'fulfilled') {
    const catData = catRes.value.data?.data ?? []
    categoryOption.value = {
      animation: false,
      tooltip: { trigger: 'item' },
      legend: { bottom: 0, type: 'scroll' },
      series: [{
        name: '文章分类',
        type: 'pie',
        radius: ['45%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: { borderRadius: 8, borderColor: 'var(--surface)', borderWidth: 2 },
        label: { show: false, position: 'center' },
        emphasis: { label: { show: true, fontSize: 16, fontWeight: 'bold' } },
        labelLine: { show: false },
        data: catData.map((i: any) => ({ value: i.article_count, name: i.category_name })),
      }],
    }
  } else {
    hasError = true
  }

  if (hasError) {
    toast.warning('部分统计数据暂不可用，已降级展示')
  }
}

const readStatisticsCache = (): StatisticsCachePayload | null => {
  try {
    const raw = sessionStorage.getItem(STATS_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as StatisticsCachePayload
    if (!parsed || typeof parsed.timestamp !== 'number') return null
    if (Date.now() - parsed.timestamp > STATS_CACHE_TTL_MS) return null
    return parsed
  } catch {
    return null
  }
}

const writeStatisticsCache = () => {
  const payload: StatisticsCachePayload = {
    timestamp: Date.now(),
    trendMetric: trendMetric.value,
    trendPeriod: trendPeriod.value,
    trendOption: trendOption.value,
    apiOption: apiOption.value,
    categoryOption: categoryOption.value,
  }
  try {
    sessionStorage.setItem(STATS_CACHE_KEY, JSON.stringify(payload))
  } catch {
  }
}

const initStatistics = async () => {
  const cache = readStatisticsCache()
  if (cache) {
    trendMetric.value = cache.trendMetric
    trendPeriod.value = cache.trendPeriod
    trendOption.value = cache.trendOption
    apiOption.value = cache.apiOption
    categoryOption.value = cache.categoryOption
    chartsReady.value = true
    backgroundRefreshTimer = window.setTimeout(() => {
      backgroundRefreshTimer = null
      void Promise.all([fetchTrendData(), fetchOtherData()]).then(() => {
        chartsReady.value = true
        writeStatisticsCache()
      })
    }, 260)
    return
  }

  await Promise.all([fetchTrendData(), fetchOtherData()])
  chartsReady.value = true
  writeStatisticsCache()
}

onMounted(async () => {
  await initStatistics()
})

onBeforeUnmount(() => {
  if (trendDebounceTimer !== null) {
    window.clearTimeout(trendDebounceTimer)
    trendDebounceTimer = null
  }
  if (backgroundRefreshTimer !== null) {
    window.clearTimeout(backgroundRefreshTimer)
    backgroundRefreshTimer = null
  }
})
</script>
