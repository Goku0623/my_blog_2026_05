<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--text)]">分类管理</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">维护文章分类，支持新增、编辑和删除</p>
      </div>
    </div>

    <UCard padding="md">
      <form class="grid grid-cols-1 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] gap-3 items-end" @submit.prevent="handleSubmit">
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">分类名称</label>
          <UInput v-model="form.name" placeholder="例如：后端开发" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">描述</label>
          <UInput v-model="form.description" placeholder="可选描述" />
        </div>
        <div class="flex gap-2">
          <UButton variant="primary" type="submit" :loading="submitting">
            {{ editingId ? '保存修改' : '新增分类' }}
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
              <th class="px-4 py-2.5 text-left font-medium">描述</th>
              <th class="px-4 py-2.5 text-center font-medium w-24">文章数</th>
              <th class="px-4 py-2.5 text-right font-medium w-40">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="p-12 text-center"><USpinner /></td>
            </tr>
            <tr v-else-if="!categories.length">
              <td colspan="6"><UEmpty title="暂无分类" description="先创建一个分类吧" class="py-12" /></td>
            </tr>
            <tr
              v-for="item in categories"
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
              <td class="px-4 py-3 text-[var(--text-soft)]">{{ item.description || '-' }}</td>
              <td class="px-4 py-3 text-center text-[var(--text-soft)]">{{ item.article_count || 0 }}</td>
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
import {
  getCategories, createCategory, updateCategory, deleteCategory, type Category,
} from '@/api/articles'
import { UCard, UInput, UButton, UEmpty, USpinner, toast, confirmDialog } from '@/ui'

const loading = ref(false)
const submitting = ref(false)
const editingId = ref<number | null>(null)
const categories = ref<Category[]>([])

const form = reactive({
  name: '',
  description: '',
})

const buildSlug = (rawName: string) => {
  const normalized = rawName
    .trim()
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  return normalized || `cat-${Date.now().toString(36)}`
}

const fetchCategories = async () => {
  loading.value = true
  try {
    const res = await getCategories()
    categories.value = res.data?.data ?? []
  } catch {
    toast.error('获取分类失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  editingId.value = null
  form.name = ''
  form.description = ''
}

const startEdit = (item: Category) => {
  editingId.value = item.id
  form.name = item.name
  form.description = item.description ?? ''
}

const handleSubmit = async () => {
  const name = form.name.trim()
  if (!name) {
    toast.warning('请输入分类名称')
    return
  }

  try {
    submitting.value = true
    if (editingId.value) {
      await updateCategory(editingId.value, {
        name,
        slug: buildSlug(name),
        description: form.description.trim() || undefined,
      })
      toast.success('分类更新成功')
    } else {
      await createCategory({
        name,
        slug: buildSlug(name),
        description: form.description.trim() || undefined,
      })
      toast.success('分类创建成功')
    }
    resetForm()
    await fetchCategories()
  } catch {
    toast.error(editingId.value ? '分类更新失败' : '分类创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (item: Category) => {
  const ok = await confirmDialog({
    title: '删除分类',
    message: `确定要删除分类「${item.name}」吗？`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return

  try {
    await deleteCategory(item.id)
    toast.success('分类已删除')
    if (editingId.value === item.id) {
      resetForm()
    }
    await fetchCategories()
  } catch {
    toast.error('分类删除失败')
  }
}

onMounted(fetchCategories)
</script>
