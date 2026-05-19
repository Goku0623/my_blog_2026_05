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
            <UInput v-model="form.DEFAULT_ARTICLE_COVER_IMAGE" placeholder="图片 URL（本地上传后自动填入）" />
            <div class="mt-2 flex flex-wrap gap-2">
              <input ref="defaultCoverInputRef" type="file" accept="image/*" class="hidden"
                @change="handleDefaultCoverFileChange" />
              <UButton variant="outline" :loading="defaultCoverUploading" @click="handleSelectDefaultCover">
                <template #icon>
                  <ImagePlus class="size-4" />
                </template>
                选择图片
              </UButton>
              <UButton variant="outline" :disabled="!defaultCoverFetchUrl.trim()" :loading="defaultCoverFetching" @click="handleFetchDefaultCoverUrl">
                从 URL 上传
              </UButton>
              <UButton v-if="form.DEFAULT_ARTICLE_COVER_IMAGE" variant="ghost" @click="clearDefaultCover">
                <template #icon>
                  <Trash2 class="size-4" />
                </template>
                清除
              </UButton>
            </div>
            <UInput v-model="defaultCoverFetchUrl" placeholder="输入图片 URL，再点「从 URL 上传」" class="mt-2" />
            <p class="mt-1 text-xs text-[var(--text-muted)]">
              上传后图片将自动保存到媒体库，并生成 16:9 缩略图；最大约 {{ defaultCoverMaxSizeMb }}MB
            </p>
            <img v-if="form.DEFAULT_ARTICLE_COVER_IMAGE" :src="form.DEFAULT_ARTICLE_COVER_IMAGE"
              class="mt-2 w-full max-h-40 object-cover rounded-lg border border-[var(--border)]" />
          </Field>
          <Field label="ICP 备案号">
            <UInput v-model="form.ICP_NUMBER" placeholder="例如：京ICP备xxxxxx号" />
          </Field>
          <Field label="关于我·正文内容">
            <UInput v-model="form.ABOUT_ME_CONTENT" type="textarea" :rows="5"
              placeholder="在此输入「关于本站」的介绍文字，支持换行（Shift+Enter）" />
            <p class="mt-1 text-xs text-[var(--text-muted)]">将显示在「关于我」页面的"关于本站"区块中</p>
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
          <Field label="天气城市名称">
            <UInput v-model="form.WEATHER_CITY_NAME" placeholder="例如：深圳市" />
          </Field>
          <Field label="天气城市代码">
            <div class="flex flex-wrap items-center gap-2">
              <UInput v-model="form.WEATHER_CITY_CODE" placeholder="例如：440300（高德 adcode）" class="w-56" />
              <UButton
                variant="outline"
                size="sm"
                :loading="cityLookupLoading"
                :disabled="!form.WEATHER_CITY_NAME.trim()"
                @click="handleLookupWeatherCityCode"
              >
                自动查询代码
              </UButton>
            </div>
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
import { lookupWeatherCityCode } from '@/api/ai'
import { uploadMediaImage, fetchMediaImage } from '@/api/media'
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
  WEATHER_CITY_NAME: string
  WEATHER_CITY_CODE: string
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
  ABOUT_ME_CONTENT: string
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
  WEATHER_CITY_NAME: '深圳市',
  WEATHER_CITY_CODE: '440300',
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
  ABOUT_ME_CONTENT: '',
})

const boolForm = reactive({
  COMMENT_ENABLED: true,
  AI_ENABLED: true,
})

const saving = ref(false)
const cityLookupLoading = ref(false)
const defaultCoverInputRef = ref<HTMLInputElement | null>(null)
const defaultCoverUploading = ref(false)
const defaultCoverFetching = ref(false)
const defaultCoverFetchUrl = ref('')
const defaultCoverMaxSizeMb = computed(() => {
  const parsed = Number(form.COVER_IMAGE_MAX_SIZE_MB)
  if (!Number.isFinite(parsed)) return 2
  return Math.min(20, Math.max(1, Math.floor(parsed)))
})

const handleSelectDefaultCover = () => {
  defaultCoverInputRef.value?.click()
}

const clearDefaultCover = () => {
  form.DEFAULT_ARTICLE_COVER_IMAGE = ''
}

const handleDefaultCoverFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  try {
    defaultCoverUploading.value = true
    const res = await uploadMediaImage(file, 'cover')
    const url = res.data?.data?.url
    if (!url) throw new Error('no url returned')
    form.DEFAULT_ARTICLE_COVER_IMAGE = url
    toast.success('封面图已上传到媒体库')
  } catch {
    toast.error('封面图上传失败，请重试')
  } finally {
    defaultCoverUploading.value = false
    target.value = ''
  }
}

const handleFetchDefaultCoverUrl = async () => {
  const url = defaultCoverFetchUrl.value.trim()
  if (!url) {
    toast.warning('请输入图片 URL')
    return
  }
  if (!/^https?:\/\//i.test(url)) {
    toast.warning('仅支持 http/https URL')
    return
  }
  try {
    defaultCoverFetching.value = true
    const res = await fetchMediaImage(url, 'cover')
    const resultUrl = res.data?.data?.url
    if (!resultUrl) throw new Error('no url returned')
    form.DEFAULT_ARTICLE_COVER_IMAGE = resultUrl
    defaultCoverFetchUrl.value = ''
    toast.success('图片已抓取并保存到媒体库')
  } catch {
    toast.error('URL 图片抓取失败，请检查链接是否可访问')
  } finally {
    defaultCoverFetching.value = false
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
    defaultCoverFetchUrl.value = ''
  } catch {
    toast.error('获取系统配置失败')
  }
}

const handleSave = async () => {
  try {
    saving.value = true
    const updatePayload = [
      ...Object.keys(form).map((key) => ({
        key,
        value: String((form as any)[key] ?? ''),
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

const handleLookupWeatherCityCode = async () => {
  const keyword = form.WEATHER_CITY_NAME.trim()
  if (!keyword) {
    toast.warning('请先输入城市名称')
    return
  }
  try {
    cityLookupLoading.value = true
    const res = await lookupWeatherCityCode(keyword)
    const payload = res.data?.data
    if (!payload?.code) {
      toast.warning('未查询到城市代码')
      return
    }
    form.WEATHER_CITY_NAME = payload.name || keyword
    form.WEATHER_CITY_CODE = payload.code
    toast.success(`已回填城市代码：${payload.code}`)
  } catch {
    toast.error('城市代码查询失败，请检查天气 API Key 或城市名称')
  } finally {
    cityLookupLoading.value = false
  }
}

onMounted(async () => {
  await fetchConfigs()
})
</script>
