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
          <label class="text-sm font-medium text-[var(--text-soft)]">分类（可选）</label>
          <UInput v-model="form.category" placeholder="例如：广告/辱骂/政治" class="w-56" />
        </div>
        <UButton variant="primary" type="submit" :loading="adding">
          <template #icon><Plus class="size-4" /></template>
          添加
        </UButton>
      </form>
    </UCard>

    <UCard padding="md">
      <div class="space-y-2">
        <label class="text-sm font-medium text-[var(--text-soft)]">JSON 批量导入</label>
        <UInput
          v-model="importJsonText"
          type="textarea"
          :rows="9"
          placeholder='[
  { "word": "垃圾", "category": "辱骂" },
  { "word": "博彩", "category": "广告" },
  { "word": "敏感词示例" }
]'
        />
        <p class="text-xs text-[var(--text-muted)]">
          可直接复制示例 JSON 后修改。字段说明：`word` 必填，`category` 可选。
        </p>
        <div class="flex gap-2">
          <UButton variant="outline" @click="fillImportExample">填入示例</UButton>
          <UButton variant="primary" :loading="importing" @click="importWordsByJson">开始导入</UButton>
        </div>
      </div>
    </UCard>

    <UCard padding="none">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium w-16">#</th>
              <th class="px-4 py-2.5 text-left font-medium">敏感词</th>
              <th class="px-4 py-2.5 text-left font-medium w-40">分类</th>
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
                <UTag variant="info">{{ w.category || '未分类' }}</UTag>
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
  getSensitiveWords, addSensitiveWord, importSensitiveWords, deleteSensitiveWord, refreshSensitiveWordsCache,
  type SensitiveWord,
} from '@/api/system'
import { UCard, UInput, UButton, UTag, UEmpty, USpinner, toast, confirmDialog } from '@/ui'

const words = ref<SensitiveWord[]>([])
const loading = ref(false)
const refreshing = ref(false)
const adding = ref(false)
const importing = ref(false)
const importJsonText = ref('')

const form = reactive({ word: '', category: '' })
const importExampleJson = `[
  { "word": "垃圾", "category": "辱骂" },
  { "word": "博彩", "category": "广告" },
  { "word": "敏感词示例" }
]`

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
    await addSensitiveWord({
      word: form.word.trim(),
      category: form.category.trim() || undefined,
    })
    toast.success('已添加')
    form.word = ''
    form.category = ''
    await fetchWords()
  } catch {
    toast.error('添加失败')
  } finally {
    adding.value = false
  }
}

const fillImportExample = () => {
  importJsonText.value = importExampleJson
}

const importWordsByJson = async () => {
  const text = importJsonText.value.trim()
  if (!text) {
    toast.warning('请先粘贴 JSON 内容')
    return
  }

  let parsed: any
  try {
    parsed = JSON.parse(text)
  } catch {
    toast.error('JSON 格式不正确，请检查后重试')
    return
  }

  if (!Array.isArray(parsed)) {
    toast.error('JSON 顶层必须是数组')
    return
  }

  const items = parsed
    .filter((item) => item && typeof item === 'object')
    .map((item) => ({
      word: String(item.word || '').trim(),
      category: typeof item.category === 'string' ? item.category.trim() : undefined,
    }))
    .filter((item) => item.word)

  if (!items.length) {
    toast.warning('未识别到有效词条，请检查 word 字段')
    return
  }

  importing.value = true
  try {
    const res = await importSensitiveWords(items)
    const created = res.data?.data?.created ?? 0
    const skipped = res.data?.data?.skipped ?? 0
    toast.success(`导入完成：新增 ${created} 条，跳过 ${skipped} 条`)
    await fetchWords()
  } catch (error: any) {
    const message = error?.response?.data?.message || '批量导入失败'
    toast.error(message)
  } finally {
    importing.value = false
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
