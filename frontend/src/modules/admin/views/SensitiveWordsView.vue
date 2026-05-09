<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--text)]">敏感词管理</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">维护评论与聊天的敏感词过滤规则</p>
      </div>
      <UButton variant="ghost" :loading="refreshing" @click="refreshCache">
        <template #icon><RotateCcw class="size-4" /></template>
        刷新缓存
      </UButton>
    </div>

    <UCard padding="md">
      <form class="flex flex-wrap gap-3 items-end" @submit.prevent="addWord">
        <div class="flex-1 min-w-[200px] space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">敏感词</label>
          <UInput v-model="form.word" placeholder="输入要屏蔽的关键词" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">严重等级</label>
          <USelect v-model="form.level" :options="levelOptions" class="w-32" />
        </div>
        <UButton variant="primary" type="submit" :loading="adding">
          <template #icon><Plus class="size-4" /></template>
          添加
        </UButton>
      </form>
    </UCard>

    <UCard padding="none">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium w-16">#</th>
              <th class="px-4 py-2.5 text-left font-medium">敏感词</th>
              <th class="px-4 py-2.5 text-left font-medium w-32">等级</th>
              <th class="px-4 py-2.5 text-left font-medium w-44">添加时间</th>
              <th class="px-4 py-2.5 text-right font-medium w-32">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="5" class="p-12 text-center"><USpinner /></td>
            </tr>
            <tr v-else-if="!words.length">
              <td colspan="5"><UEmpty title="暂无敏感词" description="添加你的第一个屏蔽词" class="py-12" /></td>
            </tr>
            <tr v-for="(w, idx) in words" :key="w.id" class="border-t border-[var(--border)] hover:bg-[var(--bg-soft)]/40">
              <td class="px-4 py-3 text-[var(--text-muted)]">{{ idx + 1 }}</td>
              <td class="px-4 py-3 font-medium text-[var(--text)]">{{ w.word }}</td>
              <td class="px-4 py-3">
                <UTag :variant="levelVariant(w.level)">{{ levelLabel(w.level) }}</UTag>
              </td>
              <td class="px-4 py-3 text-[var(--text-soft)]">{{ formatDate(w.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <UButton size="sm" variant="ghost" @click="removeWord(w.id)">删除</UButton>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { Plus, RotateCcw } from 'lucide-vue-next'
import {
  getSensitiveWords, addSensitiveWord, deleteSensitiveWord, refreshSensitiveWordsCache,
  type SensitiveWord,
} from '@/api/system'
import { UCard, UInput, USelect, UButton, UTag, UEmpty, USpinner, toast, confirmDialog } from '@/ui'

const words = ref<SensitiveWord[]>([])
const loading = ref(false)
const refreshing = ref(false)
const adding = ref(false)

const form = reactive({ word: '', level: 'medium' as 'low' | 'medium' | 'high' })

const levelOptions = [
  { label: '低', value: 'low' },
  { label: '中', value: 'medium' },
  { label: '高', value: 'high' },
]

const levelLabel = (l: string) => ({ low: '低', medium: '中', high: '高' }[l] ?? l)
const levelVariant = (l: string) =>
  l === 'high' ? 'danger' : l === 'medium' ? 'warning' : 'info'

const formatDate = (s: string) => {
  if (!s) return '-'
  const d = new Date(s)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const fetchWords = async () => {
  loading.value = true
  try {
    const res = await getSensitiveWords()
    words.value = res.data?.data ?? []
  } catch {
    toast.error('获取敏感词失败')
  } finally {
    loading.value = false
  }
}

const addWord = async () => {
  if (!form.word.trim()) {
    toast.warning('请输入敏感词')
    return
  }
  adding.value = true
  try {
    await addSensitiveWord({ word: form.word.trim(), level: form.level })
    toast.success('已添加')
    form.word = ''
    await fetchWords()
  } catch {
    toast.error('添加失败')
  } finally {
    adding.value = false
  }
}

const removeWord = async (id: number) => {
  const ok = await confirmDialog({
    title: '删除敏感词',
    message: '确定要删除该敏感词吗？',
    danger: true,
  })
  if (!ok) return
  try {
    await deleteSensitiveWord(id)
    toast.success('已删除')
    await fetchWords()
  } catch {
    toast.error('删除失败')
  }
}

const refreshCache = async () => {
  refreshing.value = true
  try {
    await refreshSensitiveWordsCache()
    toast.success('缓存已刷新')
  } catch {
    toast.error('刷新失败')
  } finally {
    refreshing.value = false
  }
}

onMounted(fetchWords)
</script>
