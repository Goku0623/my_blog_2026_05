/**
 * 格式化日期时间
 * @param date 日期字符串或 Date 对象
 * @param format 格式字符串，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的字符串
 */
export const formatDateTime = (
  date: string | Date,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string => {
  const d = typeof date === 'string' ? new Date(date) : date

  if (isNaN(d.getTime())) {
    return ''
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化日期（不含时间）
 * @param date 日期字符串或 Date 对象
 * @returns YYYY-MM-DD 格式的字符串
 */
export const formatDate = (date: string | Date): string => {
  return formatDateTime(date, 'YYYY-MM-DD')
}

/**
 * 格式化时间（不含日期）
 * @param date 日期字符串或 Date 对象
 * @returns HH:mm:ss 格式的字符串
 */
export const formatTime = (date: string | Date): string => {
  return formatDateTime(date, 'HH:mm:ss')
}

/**
 * 相对时间格式化（如：刚刚、5分钟前、2小时前、3天前）
 * @param date 日期字符串或 Date 对象
 * @returns 相对时间字符串
 */
export const formatRelativeTime = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date

  if (isNaN(d.getTime())) {
    return ''
  }

  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  const months = Math.floor(days / 30)
  const years = Math.floor(days / 365)

  if (seconds < 60) {
    return '刚刚'
  } else if (minutes < 60) {
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else if (days < 30) {
    return `${days}天前`
  } else if (months < 12) {
    return `${months}个月前`
  } else {
    return `${years}年前`
  }
}

/**
 * 获取友好的日期时间显示
 * 规则：今天显示相对时间，昨天显示"昨天 HH:mm"，更早显示完整日期
 * @param date 日期字符串或 Date 对象
 * @returns 友好的日期时间字符串
 */
export const formatFriendlyTime = (date: string | Date): string => {
  const d = typeof date === 'string' ? new Date(date) : date

  if (isNaN(d.getTime())) {
    return ''
  }

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000)
  const targetDay = new Date(d.getFullYear(), d.getMonth(), d.getDate())

  if (targetDay.getTime() === today.getTime()) {
    // 今天：显示相对时间
    return formatRelativeTime(d)
  } else if (targetDay.getTime() === yesterday.getTime()) {
    // 昨天：显示"昨天 HH:mm"
    return `昨天 ${formatTime(d).slice(0, 5)}`
  } else {
    // 更早：显示完整日期
    return formatDateTime(d, 'YYYY-MM-DD HH:mm')
  }
}

/**
 * 判断是否为今天
 * @param date 日期字符串或 Date 对象
 * @returns 是否为今天
 */
export const isToday = (date: string | Date): boolean => {
  const d = typeof date === 'string' ? new Date(date) : date
  const now = new Date()

  return (
    d.getFullYear() === now.getFullYear() &&
    d.getMonth() === now.getMonth() &&
    d.getDate() === now.getDate()
  )
}

/**
 * 判断是否为昨天
 * @param date 日期字符串或 Date 对象
 * @returns 是否为昨天
 */
export const isYesterday = (date: string | Date): boolean => {
  const d = typeof date === 'string' ? new Date(date) : date
  const yesterday = new Date()
  yesterday.setDate(yesterday.getDate() - 1)

  return (
    d.getFullYear() === yesterday.getFullYear() &&
    d.getMonth() === yesterday.getMonth() &&
    d.getDate() === yesterday.getDate()
  )
}
