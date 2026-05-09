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
          <Field label="站点 Logo">
            <UInput v-model="form.SITE_LOGO" placeholder="图片 URL" />
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
        </div>
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
import { reactive, onMounted, ref, h } from 'vue'
import { Save, Settings, ToggleRight, Cpu, Mail } from 'lucide-vue-next'
import { getAdminConfigs, bulkUpdateConfigs } from '@/api/system'
import { UCard, UInput, UButton, USelect, USwitch, toast } from '@/ui'

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
  SITE_LOGO: string
  ICP_NUMBER: string
  COMMENT_RATE_LIMIT: string
  AI_API_KEY: string
  AI_BASE_URL: string
  AI_MODEL: string
  WEATHER_API_KEY: string
  WEATHER_API_BASE_URL: string
  ADMIN_EMAIL: string
  SMTP_HOST: string
  SMTP_PORT: string
  SMTP_USER: string
  SMTP_PASSWORD: string
  SMTP_FROM: string
}

const form = reactive<ConfigForm>({
  SITE_NAME: '',
  SITE_DESCRIPTION: '',
  SITE_KEYWORDS: '',
  SITE_AUTHOR: '',
  SITE_LOGO: '',
  ICP_NUMBER: '',
  COMMENT_RATE_LIMIT: '5',
  AI_API_KEY: '',
  AI_BASE_URL: '',
  AI_MODEL: '',
  WEATHER_API_KEY: '',
  WEATHER_API_BASE_URL: '',
  ADMIN_EMAIL: '',
  SMTP_HOST: '',
  SMTP_PORT: '587',
  SMTP_USER: '',
  SMTP_PASSWORD: '',
  SMTP_FROM: '',
})

const boolForm = reactive({
  COMMENT_ENABLED: true,
  AI_ENABLED: true,
})

const saving = ref(false)

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
  } catch {
    toast.error('获取系统配置失败')
  }
}

const handleSave = async () => {
  try {
    saving.value = true
    const updatePayload = [
      ...Object.keys(form).map((key) => ({ key, value: String((form as any)[key] ?? '') })),
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
