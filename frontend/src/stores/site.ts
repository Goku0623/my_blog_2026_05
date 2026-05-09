import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSiteConfig, type SiteConfig } from '@/api/system'

export const useSiteStore = defineStore('site', () => {
  const config = ref<SiteConfig>({
    site_name: '我的博客',
    site_description: '一个基于 FastAPI + Vue3 的个人博客系统',
    site_keywords: '博客,技术,分享',
    site_author: '博主',
    admin_email: '',
    comment_enabled: true,
    comment_audit_enabled: true,
    ai_enabled: true,
  })

  const loading = ref(false)

  const fetchSiteConfig = async () => {
    try {
      loading.value = true
      const response = await getSiteConfig()
      const data = (response.data?.data ?? response.data) as Partial<SiteConfig>
      if (data && typeof data === 'object') {
        config.value = { ...config.value, ...data }
      }
    } catch (error) {
      console.warn('获取站点配置失败，使用默认配置:', error)
    } finally {
      loading.value = false
    }
  }

  // 更新站点配置（本地更新，不调用 API）
  const updateConfig = (newConfig: Partial<SiteConfig>) => {
    config.value = { ...config.value, ...newConfig }
  }

  return {
    config,
    loading,
    fetchSiteConfig,
    updateConfig,
  }
})
