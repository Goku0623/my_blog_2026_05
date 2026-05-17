<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--text)]">标签管理</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">维护文章标签，支持新增、编辑和删除</p>
      </div>
    </div>

    <UCard padding="md">
      <form class="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_180px_auto] gap-3 items-end" @submit.prevent="handleSubmit">
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">标签名称</label>
          <UInput v-model="form.name" placeholder="例如：Vue3" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">颜色（可选）</label>
          <UInput v-model="form.color" placeholder="#3b82f6" />
        </div>
        <div class="flex gap-2">
          <UButton variant="primary" type="submit" :loading="submitting">
            {{ editingId ? '保存修改' : '新增标签' }}
          </UButton>
          <UButton v-if="editingId" variant="ghost" type="button" @click="resetForm">
            取消编辑
          </UButton>
        </div>
      </form>
    </UCard>

    <UCard padding="none">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium w-20">ID</th>
              <th class="px-4 py-2.5 text-left font-medium">名称</th>
              <th class="px-4 py-2.5 text-left font-medium">Slug</th>
              <th class="px-4 py-2.5 text-left font-medium w-36">颜色</th>
              <th class="px-4 py-2.5 text-right font-medium w-40">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="5" class="p-12 text-center"><USpinner /></td>
            </tr>
            <tr v-else-if="!tags.length">
              <td colspan="5"><UEmpty title="暂无标签" description="先创建一个标签吧" class="py-12" /></td>
            </tr>
            <tr
              v-for="item in tags"
              :key="item.id"
              :class="[
                'border-t border-[var(--border)] hover:bg-[var(--bg-soft)]/40 cursor-pointer',
                editingId === item.id ? 'bg-[var(--brand)]/10' : '',
              ]"
              @click="startEdit(item)"
            >
              <td class="px-4 py-3 text-[var(--text-muted)]">{{ item.id }}</td>
              <td class="px-4 py-3 font-medium text-[var(--text)]">{{ item.name }}</td>
              <td class="px-4 py-3 text-[var(--text-soft)]">{{ item.slug }}</td>
              <td class="px-4 py-3">
                <span
                  v-if="item.color"
                  class="inline-flex items-center gap-2 text-[var(--text-soft)]"
                >
                  <span class="size-3 rounded-full border border-[var(--border)]" :style="{ backgroundColor: item.color }" />
                  {{ item.color }}
                </span>
                <span v-else class="text-[var(--text-soft)]">-</span>
              </td>
              <td class="px-4 py-3 text-right">
                <div class="inline-flex gap-1">
                  <UButton size="sm" variant="ghost" @click.stop="startEdit(item)">编辑</UButton>
                  <UButton size="sm" variant="ghost" @click.stop="handleDelete(item)">删除</UButton>
                </div>
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
import { getTags, createTag, updateTag, deleteTag, type Tag } from '@/api/articles'
import { UCard, UInput, UButton, UEmpty, USpinner, toast, confirmDialog } from '@/ui'

const loading = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const tags = ref<Tag[]>([])

const form = reactive({
  name: '',
  color: '',
})

const buildSlug = (rawName: string) => {
  const normalized = rawName
    .trim()
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  return normalized || `tag-${Date.now().toString(36)}`
}

const fetchTags = async () => {
  loading.value = true
  try {
    const res = await getTags()
    tags.value = res.data?.data ?? []
  } catch {
    toast.error('获取标签失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  editingId.value = null
  form.name = ''
  form.color = ''
}

const startEdit = (item: Tag) => {
  editingId.value = item.id
  form.name = item.name
  form.color = item.color ?? ''
}

const handleSubmit = async () => {
  const name = form.name.trim()
  if (!name) {
    toast.warning('请输入标签名称')
    return
  }

  try {
    submitting.value = true
    if (editingId.value) {
      await updateTag(editingId.value, {
        name,
        slug: buildSlug(name),
        color: form.color.trim() || undefined,
      })
      toast.success('标签更新成功')
    } else {
      await createTag({
        name,
        slug: buildSlug(name),
        color: form.color.trim() || undefined,
      })
      toast.success('标签创建成功')
    }
    resetForm()
    await fetchTags()
  } catch {
    toast.error(editingId.value ? '标签更新失败' : '标签创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (item: Tag) => {
  const ok = await confirmDialog({
    title: '删除标签',
    message: `确定要删除标签「${item.name}」吗？`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return

  try {
    await deleteTag(item.id)
    toast.success('标签已删除')
    if (editingId.value === item.id) {
      resetForm()
    }
    await fetchTags()
  } catch {
    toast.error('标签删除失败')
  }
}

onMounted(fetchTags)
</script>
