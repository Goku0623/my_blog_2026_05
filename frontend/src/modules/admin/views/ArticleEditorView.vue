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
          <div class="flex flex-wrap items-center gap-2">
            <input
              ref="contentImageInputRef"
              type="file"
              accept="image/*"
              class="hidden"
              @change="handleContentImageChange"
            />
            <UButton variant="outline" @click="handleSelectContentImage">
              <template #icon><ImagePlus class="size-4" /></template>
              插入正文图片
            </UButton>
            <p class="text-xs text-[var(--text-muted)]">
              自动压缩并以 base64 插入 Markdown（单张上限约 {{ contentImageMaxSizeMb }}MB）
            </p>
          </div>
          <div class="rounded-xl border border-[var(--border-strong)] overflow-hidden grid grid-cols-1 lg:grid-cols-2 min-h-[480px]">
            <div class="border-r border-[var(--border)] flex flex-col">
              <div class="px-3 py-2 text-xs font-medium text-[var(--text-muted)] bg-[var(--bg-soft)] border-b border-[var(--border)]">
                Markdown 编辑
              </div>
              <textarea
                ref="contentTextareaRef"
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
              <UInput v-model="coverImageUrl" placeholder="图片 URL（可选，提交时自动转 base64）" />
              <div class="flex flex-wrap gap-2">
                <input
                  ref="coverInputRef"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleCoverFileChange"
                />
                <UButton variant="outline" @click="handleSelectCover">
                  <template #icon><ImagePlus class="size-4" /></template>
                  选择图片
                </UButton>
                <UButton
                  variant="outline"
                  :disabled="!coverImageUrl.trim()"
                  @click="handleConvertCoverUrl"
                >
                  从URL转换
                </UButton>
                <UButton
                  v-if="formData.cover_image"
                  variant="ghost"
                  @click="clearCoverImage"
                >
                  <template #icon><Trash2 class="size-4" /></template>
                  清除
                </UButton>
              </div>
              <p class="text-xs text-[var(--text-muted)]">支持本地上传或 URL，最终都会以 base64 存储</p>
              <p class="text-xs text-[var(--text-muted)]">当前自动压缩上限：{{ coverMaxSizeMb }}MB</p>
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
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Save, Rocket, ChevronDown, ImagePlus, Trash2 } from 'lucide-vue-next'
import {
  getAdminArticle, createArticle, updateArticle,
  saveArticleDraftCopy, publishDraftToSource,
  getCategories, getTags, createCategory, createTag, type Category, type Tag,
} from '@/api/articles'
import { getSiteConfig } from '@/api/system'
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
const coverInputRef = ref<HTMLInputElement | null>(null)
const contentImageInputRef = ref<HTMLInputElement | null>(null)
const contentTextareaRef = ref<HTMLTextAreaElement | null>(null)
const coverImageUrl = ref('')
const coverMaxSizeMb = ref(2)
const maxCoverImageBytes = computed(() => coverMaxSizeMb.value * 1024 * 1024)
const contentImageMaxSizeMb = computed(() => Math.max(3, Math.min(10, coverMaxSizeMb.value * 2)))
const maxContentImageBytes = computed(() => contentImageMaxSizeMb.value * 1024 * 1024)
const PREVIEW_PLACEHOLDER_HTML = '<p class="text-sm text-[var(--text-muted)] text-center mt-12">在左侧输入 Markdown 内容…</p>'

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

const renderedPreview = ref(PREVIEW_PLACEHOLDER_HTML)
let previewRenderTimer: number | null = null

let autoSaveTimer: number | null = null

const renderPreview = () => {
  renderedPreview.value = formData.content ? render(formData.content) : PREVIEW_PLACEHOLDER_HTML
}

const schedulePreviewRender = (immediate = false) => {
  if (previewRenderTimer !== null) {
    window.clearTimeout(previewRenderTimer)
    previewRenderTimer = null
  }
  if (immediate) {
    renderPreview()
    return
  }
  previewRenderTimer = window.setTimeout(() => {
    previewRenderTimer = null
    renderPreview()
  }, 120)
}

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
    const [catRes, tagRes, siteRes] = await Promise.all([getCategories(), getTags(), getSiteConfig()])
    categories.value = catRes.data?.data ?? []
    tags.value = tagRes.data?.data ?? []
    const maxMb = Number(siteRes.data?.data?.cover_image_max_size_mb ?? 2)
    coverMaxSizeMb.value = Number.isFinite(maxMb) ? Math.min(20, Math.max(1, Math.floor(maxMb))) : 2
  } catch {
    toast.error('获取配置失败，已使用默认封面图大小限制')
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
    coverImageUrl.value = data.cover_image?.startsWith('http') ? data.cover_image : ''
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

const handleSelectCover = () => {
  coverInputRef.value?.click()
}

const clearCoverImage = () => {
  formData.cover_image = ''
  coverImageUrl.value = ''
}

const loadImageElement = (blob: Blob): Promise<HTMLImageElement> => {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(objectUrl)
      resolve(img)
    }
    img.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      reject(new Error('load image failed'))
    }
    img.src = objectUrl
  })
}

const compressImageBlob = async (
  blob: Blob,
  maxBytes: number,
  maxLongEdge = 0,
): Promise<Blob> => {
  const image = await loadImageElement(blob)
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('canvas unavailable')
  }

  const sourceLongEdge = Math.max(image.width, image.height)
  const baseScale = maxLongEdge > 0 && sourceLongEdge > maxLongEdge ? maxLongEdge / sourceLongEdge : 1
  const baseWidth = Math.max(1, Math.floor(image.width * baseScale))
  const baseHeight = Math.max(1, Math.floor(image.height * baseScale))

  const resampleScales = [1, 0.9, 0.8, 0.7, 0.6, 0.5]
  const qualities = [0.9, 0.82, 0.74, 0.66, 0.58, 0.5, 0.42]

  for (const scale of resampleScales) {
    const targetWidth = Math.max(1, Math.floor(baseWidth * scale))
    const targetHeight = Math.max(1, Math.floor(baseHeight * scale))
    canvas.width = targetWidth
    canvas.height = targetHeight
    ctx.clearRect(0, 0, targetWidth, targetHeight)
    ctx.drawImage(image, 0, 0, targetWidth, targetHeight)

    for (const quality of qualities) {
      const compressedBlob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', quality)
      })
      if (compressedBlob && compressedBlob.size <= maxBytes) {
        return compressedBlob
      }
    }
  }

  throw new Error('compress failed')
}

const convertBlobToCoverBase64 = async (blob: Blob, sourceLabel: string) => {
  if (!blob.type.startsWith('image/')) {
    toast.warning('请选择图片文件')
    return
  }

  let finalBlob = blob
  if (blob.size > maxCoverImageBytes.value) {
    finalBlob = await compressImageBlob(blob, maxCoverImageBytes.value)
  }

  const result = await blobToDataUrl(finalBlob)
  if (!result.startsWith('data:image/')) {
    throw new Error('invalid data url')
  }
  formData.cover_image = result
  const sizeKb = Math.round(finalBlob.size / 1024)
  toast.success(`${sourceLabel}已转换为 base64（约 ${sizeKb}KB）`)
}

const handleCoverFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    await convertBlobToCoverBase64(file, '封面图')
  } catch {
    toast.error('图片处理失败，请重试')
  } finally {
    target.value = ''
  }
}

const blobToDataUrl = (blob: Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(new Error('read blob failed'))
    reader.readAsDataURL(blob)
  })
}

const handleConvertCoverUrl = async () => {
  const url = coverImageUrl.value.trim()
  if (!url) {
    toast.warning('请输入图片 URL')
    return
  }
  if (!/^https?:\/\//i.test(url)) {
    toast.warning('仅支持 http/https URL')
    return
  }

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('fetch failed')
    }
    const blob = await response.blob()
    await convertBlobToCoverBase64(blob, 'URL 图片')
  } catch {
    // 浏览器跨域限制可能导致前端无法读取远程图片，提交时交给后端转换。
    formData.cover_image = ''
    toast.info('前端转换失败，保存时将由后端尝试转换该 URL')
  }
}

const handleSelectContentImage = () => {
  contentImageInputRef.value?.click()
}

const insertTextAtCursor = (text: string) => {
  const textarea = contentTextareaRef.value
  if (!textarea) {
    formData.content = `${formData.content}\n${text}`.trim()
    return
  }

  const start = textarea.selectionStart ?? formData.content.length
  const end = textarea.selectionEnd ?? formData.content.length
  const before = formData.content.slice(0, start)
  const after = formData.content.slice(end)
  formData.content = `${before}${text}${after}`

  requestAnimationFrame(() => {
    const cursor = start + text.length
    textarea.focus()
    textarea.setSelectionRange(cursor, cursor)
  })
}

const handleContentImageChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  try {
    let finalBlob: Blob = file
    if (file.size > maxContentImageBytes.value) {
      finalBlob = await compressImageBlob(file, maxContentImageBytes.value, 1600)
    }
    const imageDataUrl = await blobToDataUrl(finalBlob)
    if (!imageDataUrl.startsWith('data:image/')) {
      throw new Error('invalid data url')
    }

    const safeName = (file.name || 'image')
      .replace(/\.[^.]+$/, '')
      .replace(/[^\w\u4e00-\u9fa5-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '') || 'image'
    const markdown = `\n![${safeName}](${imageDataUrl})\n`
    insertTextAtCursor(markdown)
    toast.success('正文图片已插入（base64）')
  } catch {
    toast.error('正文图片处理失败，请重试')
  } finally {
    target.value = ''
  }
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
    let shouldJumpToArticles = false
    const normalizedBase64 = formData.cover_image.trim()
    const normalizedUrl = coverImageUrl.value.trim()
    const payload = {
      ...formData,
      cover_image: normalizedBase64 || normalizedUrl || null,
      status: publish ? 'published' : 'draft',
    }
    if (isEdit.value) {
      if (!publish && !isDraftCopy.value && originalStatus.value === 'published') {
        await saveArticleDraftCopy(articleId.value, payload as any)
        toast.success('已生成草稿副本，原发布文章不受影响')
        shouldJumpToArticles = true
      } else if (publish && isDraftCopy.value) {
        await publishDraftToSource(articleId.value)
        toast.success('草稿已同步到原文并发布')
        shouldJumpToArticles = true
      } else {
        await updateArticle(articleId.value, payload as any)
        if (publish) originalStatus.value = 'published'
        else originalStatus.value = 'draft'
        toast.success(publish ? '文章已更新发布' : '草稿已保存')
        shouldJumpToArticles = true
      }
    } else {
      await createArticle(payload as any)
      localStorage.removeItem('article_draft')
      toast.success(publish ? '文章已发布' : '草稿已保存')
      shouldJumpToArticles = true
    }
    lastSaved.value = formatDateTime(new Date().toISOString())
    if (shouldJumpToArticles) {
      router.push('/admin/articles')
    }
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

watch(() => formData.content, () => {
  schedulePreviewRender()
}, { immediate: true })

onUnmounted(() => {
  if (autoSaveTimer) window.clearInterval(autoSaveTimer)
  if (previewRenderTimer !== null) {
    window.clearTimeout(previewRenderTimer)
    previewRenderTimer = null
  }
})
</script>
