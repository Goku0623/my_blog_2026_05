<template>
  <div class="space-y-4">
    <!-- 顶部 -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--text)]">{{ isEdit ? '编辑文章' : '新建文章' }}</h1>
        <p class="text-xs text-[var(--text-muted)] mt-1" v-if="lastSaved">上次保存：{{ lastSaved }}</p>
      </div>
      <div class="flex items-center gap-2">
        <UButton variant="ghost" :loading="saving" @click="handleSaveDraft">
          <template #icon><Save class="size-4" /></template>
          保存草稿
        </UButton>
        <UButton variant="primary" :loading="saving" @click="handlePublish">
          <template #icon><Rocket class="size-4" /></template>
          {{ isDraftCopy ? '同步并发布' : (formData.status === 'published' ? '更新发布' : '发布文章') }}
        </UButton>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_320px] gap-4">
      <!-- 主编辑区 -->
      <UCard padding="md" body-class="space-y-4">
        <div class="space-y-1.5">
          <label class="text-sm font-medium">文章标题 <span class="text-rose-500">*</span></label>
          <UInput v-model="formData.title" placeholder="请输入文章标题" :maxlength="200" show-count />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">文章内容 <span class="text-rose-500">*</span></label>
          <div class="rounded-xl border border-[var(--border-strong)] overflow-hidden grid grid-cols-1 lg:grid-cols-2 min-h-[480px]">
            <div class="border-r border-[var(--border)] flex flex-col">
              <div class="px-3 py-2 text-xs font-medium text-[var(--text-muted)] bg-[var(--bg-soft)] border-b border-[var(--border)]">
                Markdown 编辑
              </div>
              <textarea
                v-model="formData.content"
                placeholder="支持 Markdown 语法…"
                class="flex-1 w-full p-4 bg-[var(--surface)] text-[var(--text)] font-mono text-sm leading-relaxed outline-none resize-none"
              />
            </div>
            <div class="flex flex-col bg-[var(--bg-soft)]">
              <div class="px-3 py-2 text-xs font-medium text-[var(--text-muted)] bg-[var(--bg-soft)] border-b border-[var(--border)]">
                实时预览
              </div>
              <div class="flex-1 p-4 overflow-y-auto prose prose-sm max-w-none dark:prose-invert" v-html="renderedPreview" />
            </div>
          </div>
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium">文章摘要</label>
          <UInput
            v-model="formData.summary"
            type="textarea"
            :rows="3"
            placeholder="为空时将自动从内容前 100 字提取"
          />
        </div>
      </UCard>

      <!-- 侧栏 -->
      <div class="space-y-4">
        <UCard padding="md">
          <template #header><span class="font-semibold">基础设置</span></template>
          <div class="space-y-3">
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">分类 <span class="text-rose-500">*</span></label>
              <USelect
                v-model="formData.category_id"
                :options="categories.map(c => ({ label: c.name, value: c.id }))"
                placeholder="选择分类"
              />
              <div class="flex gap-2">
                <UInput
                  v-model="newCategoryName"
                  placeholder="输入新分类名称"
                  :disabled="creatingCategory"
                  @keyup.enter="handleCreateCategory"
                />
                <UButton
                  variant="outline"
                  :loading="creatingCategory"
                  :disabled="!newCategoryName.trim()"
                  @click="handleCreateCategory"
                >
                  新建分类
                </UButton>
              </div>
            </div>
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">标签</label>
              <div class="flex flex-wrap gap-1.5 rounded-lg border border-[var(--border-strong)] bg-[var(--surface)] p-2 min-h-[40px]">
                <UTag
                  v-for="tag in tags"
                  :key="tag.id"
                  :variant="formData.tag_ids.includes(tag.id) ? 'brand' : 'outline'"
                  class="cursor-pointer"
                  @click="toggleTag(tag.id)"
                >
                  #{{ tag.name }}
                </UTag>
              </div>
              <div class="flex gap-2">
                <UInput
                  v-model="newTagName"
                  placeholder="输入新标签名称"
                  :disabled="creatingTag"
                  @keyup.enter="handleCreateTag"
                />
                <UButton
                  variant="outline"
                  :loading="creatingTag"
                  :disabled="!newTagName.trim()"
                  @click="handleCreateTag"
                >
                  新建标签
                </UButton>
              </div>
            </div>
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">封面图</label>
              <UInput v-model="formData.cover_image" placeholder="图片 URL" />
              <img
                v-if="formData.cover_image"
                :src="formData.cover_image"
                class="mt-2 w-full max-h-40 object-cover rounded-lg border border-[var(--border)]"
              />
            </div>
            <div class="flex items-center justify-between">
              <label class="text-sm text-[var(--text)]">精选阅读</label>
              <USwitch v-model="formData.is_featured" />
            </div>
            <div class="flex items-center justify-between">
              <label class="text-sm text-[var(--text)]">允许评论</label>
              <USwitch v-model="formData.allow_comment" />
            </div>
          </div>
        </UCard>

        <UCard padding="md">
          <template #header>
            <button
              class="flex items-center justify-between w-full font-semibold"
              @click="seoOpen = !seoOpen"
            >
              <span>SEO 设置</span>
              <ChevronDown :class="['size-4 transition-transform', seoOpen ? 'rotate-180' : '']" />
            </button>
          </template>
          <div v-if="seoOpen" class="space-y-3">
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">SEO 标题</label>
              <UInput v-model="formData.seo_title" placeholder="可选" />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">SEO 关键词</label>
              <UInput v-model="formData.seo_keywords" placeholder="以英文逗号分隔" />
            </div>
            <div class="space-y-1.5">
              <label class="text-xs text-[var(--text-soft)]">SEO 描述</label>
              <UInput v-model="formData.seo_description" type="textarea" :rows="3" placeholder="可选" />
            </div>
          </div>
        </UCard>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Save, Rocket, ChevronDown } from 'lucide-vue-next'
import {
  getAdminArticle, createArticle, updateArticle,
  saveArticleDraftCopy, publishDraftToSource,
  getCategories, getTags, createCategory, createTag, type Category, type Tag,
} from '@/api/articles'
import { useMarkdown } from '@/composables/useMarkdown'
import { formatDateTime } from '@/utils/time'
import { UCard, UInput, USelect, USwitch, UButton, UTag, toast } from '@/ui'

const route = useRoute()
const router = useRouter()
const { render } = useMarkdown()

const isEdit = computed(() => !!route.params.id)
const articleId = computed(() => Number(route.params.id))

const saving = ref(false)
const lastSaved = ref('')
const seoOpen = ref(false)
const originalStatus = ref('draft')
const isDraftCopy = ref(false)
const sourceArticleId = ref<number | null>(null)

const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])
const newCategoryName = ref('')
const newTagName = ref('')
const creatingCategory = ref(false)
const creatingTag = ref(false)

const formData = reactive({
  title: '',
  content: '',
  summary: '',
  category_id: undefined as number | undefined,
  tag_ids: [] as number[],
  cover_image: '',
  is_featured: false,
  allow_comment: true,
  status: 'draft',
  seo_title: '',
  seo_keywords: '',
  seo_description: '',
})

const renderedPreview = computed(() =>
  formData.content
    ? render(formData.content)
    : '<p class="text-sm text-[var(--text-muted)] text-center mt-12">在左侧输入 Markdown 内容…</p>'
)

let autoSaveTimer: number | null = null

const createSlug = (rawName: string, prefix: 'cat' | 'tag') => {
  const normalized = rawName
    .trim()
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')

  if (normalized) return normalized
  return `${prefix}-${Date.now().toString(36)}`
}

const fetchMetadata = async () => {
  try {
    const [catRes, tagRes] = await Promise.all([getCategories(), getTags()])
    categories.value = catRes.data?.data ?? []
    tags.value = tagRes.data?.data ?? []
  } catch {
    toast.error('获取分类或标签失败')
  }
}

const fetchArticle = async () => {
  if (!isEdit.value) return
  try {
    const res = await getAdminArticle(articleId.value)
    const data: any = res.data?.data ?? {}
    formData.title = data.title ?? ''
    formData.content = data.content ?? ''
    formData.summary = data.summary ?? ''
    formData.category_id = data.category?.id ?? data.category_id
    formData.tag_ids = (data.tags ?? []).map((t: any) => t.id)
    formData.cover_image = data.cover_image ?? ''
    formData.is_featured = data.is_featured === true
    formData.status = data.status ?? 'draft'
    originalStatus.value = data.status ?? 'draft'
    isDraftCopy.value = Boolean(data.is_draft_copy)
    sourceArticleId.value = data.source_article_id ?? null
    formData.allow_comment = data.allow_comment !== false
    formData.seo_title = data.seo_title ?? ''
    formData.seo_keywords = data.seo_keywords ?? ''
    formData.seo_description = data.seo_description ?? ''
  } catch {
    toast.error('获取文章详情失败')
  }
}

const toggleTag = (id: number) => {
  const idx = formData.tag_ids.indexOf(id)
  if (idx >= 0) formData.tag_ids.splice(idx, 1)
  else formData.tag_ids.push(id)
}

const handleCreateCategory = async () => {
  const name = newCategoryName.value.trim()
  if (!name) {
    toast.warning('请输入分类名称')
    return
  }
  try {
    creatingCategory.value = true
    const payload = { name, slug: createSlug(name, 'cat') }
    const res = await createCategory(payload)
    await fetchMetadata()
    const createdId = res.data?.data?.id
    const matched = categories.value.find((c) => c.name === name)
    formData.category_id = createdId ?? matched?.id ?? formData.category_id
    newCategoryName.value = ''
    toast.success('分类创建成功')
  } catch {
    toast.error('分类创建失败')
  } finally {
    creatingCategory.value = false
  }
}

const handleCreateTag = async () => {
  const name = newTagName.value.trim()
  if (!name) {
    toast.warning('请输入标签名称')
    return
  }
  try {
    creatingTag.value = true
    const payload = { name, slug: createSlug(name, 'tag') }
    const res = await createTag(payload)
    await fetchMetadata()
    const createdId = res.data?.data?.id
    const matched = tags.value.find((t) => t.name === name)
    const targetId = createdId ?? matched?.id
    if (targetId && !formData.tag_ids.includes(targetId)) {
      formData.tag_ids.push(targetId)
    }
    newTagName.value = ''
    toast.success('标签创建成功')
  } catch {
    toast.error('标签创建失败')
  } finally {
    creatingTag.value = false
  }
}

const saveLocalDraft = () => {
  if (isEdit.value) return
  localStorage.setItem('article_draft', JSON.stringify(formData))
  lastSaved.value = formatDateTime(new Date().toISOString())
}

const loadLocalDraft = () => {
  if (isEdit.value) return
  const raw = localStorage.getItem('article_draft')
  if (!raw) return
  try {
    Object.assign(formData, JSON.parse(raw))
    toast.info('已恢复本地草稿')
  } catch { /* ignore */ }
}

const validate = () => {
  if (!formData.title.trim()) {
    toast.warning('请输入文章标题')
    return false
  }
  if (!formData.content.trim()) {
    toast.warning('请输入文章内容')
    return false
  }
  if (!formData.category_id) {
    toast.warning('请选择文章分类')
    return false
  }
  return true
}

const submit = async (publish: boolean) => {
  if (!validate()) return

  try {
    saving.value = true
    const payload = {
      ...formData,
      status: publish ? 'published' : 'draft',
    }
    if (isEdit.value) {
      if (!publish && !isDraftCopy.value && originalStatus.value === 'published') {
        const res = await saveArticleDraftCopy(articleId.value, payload as any)
        const draftId = res.data?.data?.id
        toast.success('已生成草稿副本，原发布文章不受影响')
        if (draftId) {
          router.replace(`/admin/articles/edit/${draftId}`)
        }
      } else if (publish && isDraftCopy.value) {
        await publishDraftToSource(articleId.value)
        toast.success('草稿已同步到原文并发布')
        if (sourceArticleId.value) {
          router.replace(`/admin/articles/edit/${sourceArticleId.value}`)
        } else {
          router.push('/admin/articles')
        }
      } else {
        await updateArticle(articleId.value, payload as any)
        if (publish) originalStatus.value = 'published'
        else originalStatus.value = 'draft'
        toast.success(publish ? '文章已更新发布' : '草稿已保存')
      }
    } else {
      await createArticle(payload as any)
      localStorage.removeItem('article_draft')
      toast.success(publish ? '文章已发布' : '草稿已保存')
      router.push('/admin/articles')
    }
    lastSaved.value = formatDateTime(new Date().toISOString())
  } catch {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleSaveDraft = () => submit(false)
const handlePublish = () => submit(true)

onMounted(async () => {
  await fetchMetadata()
  if (isEdit.value) {
    await fetchArticle()
  } else {
    loadLocalDraft()
    autoSaveTimer = window.setInterval(saveLocalDraft, 30000)
  }
})

onUnmounted(() => {
  if (autoSaveTimer) window.clearInterval(autoSaveTimer)
})
</script>
