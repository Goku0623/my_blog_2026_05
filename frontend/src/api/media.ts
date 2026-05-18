import request from './index'

export type MediaPurpose = 'cover' | 'content'

export interface MediaUploadResult {
  url: string
  size?: number | null
  width?: number | null
  height?: number | null
}

export const uploadMediaImage = (file: File, purpose: MediaPurpose = 'content') => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<{ data: MediaUploadResult }>(`/admin/media/upload?purpose=${purpose}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}

export const fetchMediaImage = (url: string, purpose: MediaPurpose = 'content') => {
  return request.post<{ data: MediaUploadResult }>('/admin/media/fetch', {
    url,
    purpose,
  })
}
