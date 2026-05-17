<template>
  <div class="space-y-4">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-xl font-semibold text-[var(--text)]">系统配置</h1>
        <p class="text-sm text-[var(--text-muted)] mt-1">站点信息、功能开关与第三方集成</p>
      </div>
      <UButton variant="primary" :loading="saving" @click="handleSave">
        <template #icon>
          <Save class="size-4" />
        </template>
        保存全部
      </UButton>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- 基础信息 -->
      <UCard padding="md">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <Settings class="size-4 text-[var(--brand)]" /> 站点信息
          </div>
        </template>
        <div class="space-y-4">
          <Field label="站点名称">
            <UInput v-model="form.SITE_NAME" placeholder="例如：我的博客" />
          </Field>
          <Field label="站点描述">
            <UInput v-model="form.SITE_DESCRIPTION" type="textarea" :rows="2" placeholder="一句话简介" />
          </Field>
          <Field label="站点关键词">
            <UInput v-model="form.SITE_KEYWORDS" placeholder="以英文逗号分隔" />
          </Field>
          <Field label="站点作者">
            <UInput v-model="form.SITE_AUTHOR" />
          </Field>
          <Field label="默认文章封面图">
            <UInput v-model="defaultCoverImageUrl" placeholder="图片 URL（可选，保存时自动转换）" />
            <div class="mt-2 flex flex-wrap gap-2">
              <input ref="defaultCoverInputRef" type="file" accept="image/*" class="hidden"
                @change="handleDefaultCoverFileChange" />
              <UButton variant="outline" @click="handleSelectDefaultCover">
                <template #icon>
                  <ImagePlus class="size-4" />
                </template>
                选择图片
              </UButton>
              <UButton variant="outline" :disabled="!defaultCoverImageUrl.trim()" @click="handleConvertDefaultCoverUrl">
                从 URL 转换
              </UButton>
              <UButton v-if="defaultCoverPreview" variant="ghost" @click="clearDefaultCover">
                <template #icon>
                  <Trash2 class="size-4" />
                </template>
                清除
              </UButton>
            </div>
            <p class="mt-1 text-xs text-[var(--text-muted)]">
              支持本地上传或 URL，保存后将自动生成 16:9 缩略图；最大约 {{ defaultCoverMaxSizeMb }}MB
            </p>
            <img v-if="defaultCoverPreview" :src="defaultCoverPreview"
              class="mt-2 w-full max-h-40 object-cover rounded-lg border border-[var(--border)]" />
          </Field>
          <Field label="ICP 备案号">
            <UInput v-model="form.ICP_NUMBER" placeholder="例如：京ICP备xxxxxx号" />
          </Field>
        </div>
      </UCard>

      <!-- 功能开关 -->
      <UCard padding="md">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <ToggleRight class="size-4 text-[var(--brand)]" /> 功能开关
          </div>
        </template>
        <div class="space-y-4">
          <ToggleRow v-model="boolForm.COMMENT_ENABLED" label="评论功能" description="是否允许访客在文章下方留言" />
          <ToggleRow v-model="boolForm.AI_ENABLED" label="AI 助手" description="是否启用评论 AI 回复建议能力" />
          <Field label="评论速率限制">
            <div class="flex items-center gap-2">
              <UInput v-model="form.COMMENT_RATE_LIMIT" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">条 / 分钟</span>
            </div>
          </Field>
          <Field label="评论每日上限（每用户）">
            <div class="flex items-center gap-2">
              <UInput v-model="form.COMMENT_DAILY_LIMIT_PER_USER" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">条 / 天（0 表示不限额）</span>
            </div>
          </Field>
          <Field label="评论每日上限（每文章每用户）">
            <div class="flex items-center gap-2">
              <UInput v-model="form.COMMENT_DAILY_LIMIT_PER_ARTICLE_PER_USER" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">条 / 天（0 表示不限额）</span>
            </div>
          </Field>
          <Field label="留言墙每日上限（每用户）">
            <div class="flex items-center gap-2">
              <UInput v-model="form.GUESTBOOK_DAILY_LIMIT_PER_USER" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">条 / 天（0 表示不限额）</span>
            </div>
          </Field>
          <Field label="封面图最大体积">
            <div class="flex items-center gap-2">
              <UInput v-model="form.COVER_IMAGE_MAX_SIZE_MB" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">MB（建议 1-20）</span>
            </div>
          </Field>
        </div>
      </UCard>

      <!-- AI 配置 -->
      <UCard padding="md" class="lg:col-span-2">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <Cpu class="size-4 text-[var(--brand)]" /> AI 大模型配置
          </div>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="API Key">
            <UInput v-model="form.AI_API_KEY" type="password" placeholder="请输入大模型 API Key" />
          </Field>
          <Field label="Base URL">
            <UInput v-model="form.AI_BASE_URL" placeholder="https://api.openai.com/v1" />
          </Field>
          <Field label="模型名称">
            <UInput v-model="form.AI_MODEL" placeholder="例如：gpt-4o-mini, gemini-pro" />
          </Field>
          <Field label="天气 API Key">
            <UInput v-model="form.WEATHER_API_KEY" />
          </Field>
          <Field label="天气 API 地址">
            <UInput v-model="form.WEATHER_API_BASE_URL" placeholder="可选，默认留空使用内置地址" />
          </Field>
          <Field label="助手 Webhook URL">
            <UInput v-model="form.N8N_ASSISTANT_WEBHOOK_URL" placeholder="https://your-n8n/webhook/assistant-chat" />
          </Field>
          <Field label="X-N8N-Secret">
            <UInput v-model="form.N8N_SECRET" type="password"
              placeholder="用于 /ai/n8n/article 与 /assistant/chat 的 X-N8N-Secret" />
          </Field>
          <Field label="游客每日提问限额">
            <div class="flex items-center gap-2">
              <UInput v-model="form.ASSISTANT_GUEST_DAILY_LIMIT" type="number" class="w-32" />
              <span class="text-sm text-[var(--text-muted)]">次 / 天（0 表示不限额）</span>
            </div>
          </Field>
        </div>
      </UCard>

      <!-- N8N 博客入库配置 -->
      <UCard padding="md" class="lg:col-span-2">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <Globe class="size-4 text-[var(--brand)]" /> N8N 博客文章入库
          </div>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="Blog Ingest Webhook URL">
            <UInput v-model="form.N8N_BLOG_INGEST_WEBHOOK_URL" placeholder="https://your-n8n/webhook/blog-ingest" />
          </Field>
          <Field label="站点 URL">
            <UInput v-model="form.SITE_URL" placeholder="https://example.com" />
          </Field>
        </div>
        <p class="mt-3 text-xs text-[var(--text-muted)]">
          当文章发布或更新时，自动将文章内容发送到 N8N Webhook 存入向量数据库。密钥沿用 X-N8N-Secret。
        </p>
      </UCard>

      <!-- 社交链接 -->
      <UCard padding="md" class="lg:col-span-2">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <Link class="size-4 text-[var(--brand)]" /> 社交链接
          </div>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="GitHub URL">
            <UInput v-model="form.GITHUB_URL" placeholder="https://github.com/yourname" />
          </Field>
          <Field label="Bilibili URL">
            <UInput v-model="form.BILIBILI_URL" placeholder="https://space.bilibili.com/xxxxx" />
          </Field>
        </div>
        <p class="mt-3 text-xs text-[var(--text-muted)]">
          设置后在"关于我"页面可点击跳转。邮箱使用上方邮件配置中的管理员邮箱。
        </p>
      </UCard>

      <!-- 邮件配置 -->
      <UCard padding="md" class="lg:col-span-2">
        <template #header>
          <div class="flex items-center gap-2 font-semibold">
            <Mail class="size-4 text-[var(--brand)]" /> 邮件 / SMTP 配置
          </div>
        </template>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Field label="管理员邮箱">
            <UInput v-model="form.ADMIN_EMAIL" />
          </Field>
          <Field label="SMTP 服务器">
            <UInput v-model="form.SMTP_HOST" placeholder="smtp.example.com" />
          </Field>
          <Field label="SMTP 端口">
            <UInput v-model="form.SMTP_PORT" type="number" />
          </Field>
          <Field label="SMTP 用户名">
            <UInput v-model="form.SMTP_USER" />
          </Field>
          <Field label="SMTP 密码">
            <UInput v-model="form.SMTP_PASSWORD" type="password" />
          </Field>
          <Field label="发件人地址">
            <UInput v-model="form.SMTP_FROM" />
          </Field>
        </div>
      </UCard>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted, ref, computed, h } from 'vue'
import { Save, Settings, ToggleRight, Cpu, Mail, ImagePlus, Trash2, Globe, Link } from 'lucide-vue-next'
import { getAdminConfigs, bulkUpdateConfigs } from '@/api/system'
import { UCard, UInput, UButton, USwitch, toast } from '@/ui'

const Field = (props: any, ctx: any) =>
  h('div', { class: 'space-y-1.5' }, [
    h('label', { class: 'text-sm font-medium text-[var(--text-soft)]' }, props.label),
    ctx.slots.default?.(),
  ])

const ToggleRow = (props: any, { emit }: any) =>
  h('div', { class: 'flex items-start justify-between gap-4 py-1' }, [
    h('div', { class: 'min-w-0' }, [
      h('p', { class: 'text-sm font-medium text-[var(--text)]' }, props.label),
      h('p', { class: 'text-xs text-[var(--text-muted)] mt-0.5' }, props.description),
    ]),
    h(USwitch, {
      modelValue: props.modelValue,
      'onUpdate:modelValue': (v: boolean) => emit('update:modelValue', v),
    }),
  ])
  ; (ToggleRow as any).props = ['modelValue', 'label', 'description']
  ; (ToggleRow as any).emits = ['update:modelValue']

interface ConfigForm {
  SITE_NAME: string
  SITE_DESCRIPTION: string
  SITE_KEYWORDS: string
  SITE_AUTHOR: string
  DEFAULT_ARTICLE_COVER_IMAGE: string
  ICP_NUMBER: string
  COMMENT_RATE_LIMIT: string
  COMMENT_DAILY_LIMIT_PER_USER: string
  COMMENT_DAILY_LIMIT_PER_ARTICLE_PER_USER: string
  GUESTBOOK_DAILY_LIMIT_PER_USER: string
  COVER_IMAGE_MAX_SIZE_MB: string
  AI_API_KEY: string
  AI_BASE_URL: string
  AI_MODEL: string
  WEATHER_API_KEY: string
  WEATHER_API_BASE_URL: string
  N8N_ASSISTANT_WEBHOOK_URL: string
  N8N_SECRET: string
  ASSISTANT_GUEST_DAILY_LIMIT: string
  ADMIN_EMAIL: string
  SMTP_HOST: string
  SMTP_PORT: string
  SMTP_USER: string
  SMTP_PASSWORD: string
  SMTP_FROM: string
  N8N_BLOG_INGEST_WEBHOOK_URL: string
  SITE_URL: string
  GITHUB_URL: string
  BILIBILI_URL: string
}

const form = reactive<ConfigForm>({
  SITE_NAME: '',
  SITE_DESCRIPTION: '',
  SITE_KEYWORDS: '',
  SITE_AUTHOR: '',
  DEFAULT_ARTICLE_COVER_IMAGE: '',
  ICP_NUMBER: '',
  COMMENT_RATE_LIMIT: '5',
  COMMENT_DAILY_LIMIT_PER_USER: '2',
  COMMENT_DAILY_LIMIT_PER_ARTICLE_PER_USER: '2',
  GUESTBOOK_DAILY_LIMIT_PER_USER: '2',
  COVER_IMAGE_MAX_SIZE_MB: '2',
  AI_API_KEY: '',
  AI_BASE_URL: '',
  AI_MODEL: '',
  WEATHER_API_KEY: '',
  WEATHER_API_BASE_URL: '',
  N8N_ASSISTANT_WEBHOOK_URL: '',
  N8N_SECRET: '',
  ASSISTANT_GUEST_DAILY_LIMIT: '3',
  ADMIN_EMAIL: '',
  SMTP_HOST: '',
  SMTP_PORT: '587',
  SMTP_USER: '',
  SMTP_PASSWORD: '',
  SMTP_FROM: '',
  N8N_BLOG_INGEST_WEBHOOK_URL: '',
  SITE_URL: '',
  GITHUB_URL: '',
  BILIBILI_URL: '',
})

const boolForm = reactive({
  COMMENT_ENABLED: true,
  AI_ENABLED: true,
})

const saving = ref(false)
const defaultCoverInputRef = ref<HTMLInputElement | null>(null)
const defaultCoverImageUrl = ref('')
const defaultCoverMaxSizeMb = computed(() => {
  const parsed = Number(form.COVER_IMAGE_MAX_SIZE_MB)
  if (!Number.isFinite(parsed)) return 2
  return Math.min(20, Math.max(1, Math.floor(parsed)))
})
const maxDefaultCoverBytes = computed(() => defaultCoverMaxSizeMb.value * 1024 * 1024)
const defaultCoverPreview = computed(() =>
  form.DEFAULT_ARTICLE_COVER_IMAGE.trim() || defaultCoverImageUrl.value.trim(),
)

const blobToDataUrl = (blob: Blob): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(typeof reader.result === 'string' ? reader.result : '')
    reader.onerror = () => reject(new Error('read blob failed'))
    reader.readAsDataURL(blob)
  })

const loadImageElement = (blob: Blob): Promise<HTMLImageElement> =>
  new Promise((resolve, reject) => {
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

const compressImageBlob = async (blob: Blob, maxBytes: number): Promise<Blob> => {
  const image = await loadImageElement(blob)
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) {
    throw new Error('canvas unavailable')
  }

  const sourceLongEdge = Math.max(image.width, image.height)
  const maxLongEdge = 2000
  const baseScale = sourceLongEdge > maxLongEdge ? maxLongEdge / sourceLongEdge : 1
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

const convertBlobToDefaultCoverBase64 = async (blob: Blob, sourceLabel: string) => {
  if (!blob.type.startsWith('image/')) {
    toast.warning('请选择图片文件')
    return
  }

  let finalBlob = blob
  if (blob.size > maxDefaultCoverBytes.value) {
    finalBlob = await compressImageBlob(blob, maxDefaultCoverBytes.value)
  }

  const result = await blobToDataUrl(finalBlob)
  if (!result.startsWith('data:image/')) {
    throw new Error('invalid data url')
  }
  form.DEFAULT_ARTICLE_COVER_IMAGE = result
  defaultCoverImageUrl.value = ''
  const sizeKb = Math.round(finalBlob.size / 1024)
  toast.success(`${sourceLabel}已转换为 base64（约 ${sizeKb}KB）`)
}

const handleSelectDefaultCover = () => {
  defaultCoverInputRef.value?.click()
}

const clearDefaultCover = () => {
  form.DEFAULT_ARTICLE_COVER_IMAGE = ''
  defaultCoverImageUrl.value = ''
}

const handleDefaultCoverFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  try {
    await convertBlobToDefaultCoverBase64(file, '默认封面图')
  } catch {
    toast.error('默认封面图处理失败，请重试')
  } finally {
    target.value = ''
  }
}

const handleConvertDefaultCoverUrl = async () => {
  const url = defaultCoverImageUrl.value.trim()
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
    await convertBlobToDefaultCoverBase64(blob, 'URL 图片')
  } catch {
    form.DEFAULT_ARTICLE_COVER_IMAGE = ''
    toast.info('前端转换失败，保存时将由后端尝试转换该 URL')
  }
}

const fetchConfigs = async () => {
  try {
    const res = await getAdminConfigs()
    const list = res.data?.data ?? []
    list.forEach((item: any) => {
      if (item.key in form) {
        ; (form as any)[item.key] = item.value
      }
      if (item.key in boolForm) {
        ; (boolForm as any)[item.key] = ['true', '1', 'on'].includes(String(item.value).toLowerCase())
      }
    })
    defaultCoverImageUrl.value = /^https?:\/\//i.test(form.DEFAULT_ARTICLE_COVER_IMAGE.trim())
      ? form.DEFAULT_ARTICLE_COVER_IMAGE.trim()
      : ''
  } catch {
    toast.error('获取系统配置失败')
  }
}

const handleSave = async () => {
  try {
    saving.value = true
    const normalizedDefaultCoverData = form.DEFAULT_ARTICLE_COVER_IMAGE.trim()
    const normalizedDefaultCoverUrl = defaultCoverImageUrl.value.trim()
    const defaultCoverSubmitValue = normalizedDefaultCoverUrl || normalizedDefaultCoverData

    const updatePayload = [
      ...Object.keys(form).map((key) => ({
        key,
        value: key === 'DEFAULT_ARTICLE_COVER_IMAGE'
          ? defaultCoverSubmitValue
          : String((form as any)[key] ?? ''),
      })),
      ...Object.keys(boolForm).map((key) => ({ key, value: (boolForm as any)[key] ? 'true' : 'false' })),
    ]
    await bulkUpdateConfigs(updatePayload)
    toast.success('配置已保存')
  } catch {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  await fetchConfigs()
})
</script>
