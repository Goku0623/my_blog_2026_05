import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getGuestIdentity } from '@/api/comments'

const GUEST_TOKEN_KEY = 'guest_token'
const GUEST_NAME_KEY = 'guest_name'

const buildGuestDisplayName = (guestToken?: string, nickname?: string) => {
  if (nickname && nickname.trim()) return nickname
  const shortCode = (guestToken || '').replace(/-/g, '').toUpperCase().slice(0, 6)
  if (shortCode) return `游客${shortCode}`
  return '游客'
}

export const useGuestStore = defineStore('guest', () => {
  const guestToken = ref<string | null>(localStorage.getItem(GUEST_TOKEN_KEY))
  const guestName = ref<string>(localStorage.getItem(GUEST_NAME_KEY) || '')

  const isGuest = computed(() => !!guestToken.value)

  const fetchGuestToken = async () => {
    try {
      const response = await getGuestIdentity()
      const { guest_token, nickname } = response.data.data
      const guestDisplayName = buildGuestDisplayName(guest_token, nickname)

      guestToken.value = guest_token
      guestName.value = guestDisplayName

      localStorage.setItem(GUEST_TOKEN_KEY, guest_token)
      localStorage.setItem(GUEST_NAME_KEY, guestDisplayName)

      return guest_token
    } catch (error) {
      console.error('获取游客 token 失败:', error)
      throw error
    }
  }

  const initGuest = async () => {
    if (!guestToken.value || !guestName.value.trim()) {
      await fetchGuestToken()
    }
  }

  const clearGuest = () => {
    guestToken.value = null
    guestName.value = ''
    localStorage.removeItem(GUEST_TOKEN_KEY)
    localStorage.removeItem(GUEST_NAME_KEY)
  }

  return {
    guestToken,
    guestName,
    isGuest,
    fetchGuestToken,
    initGuest,
    clearGuest,
  }
})
