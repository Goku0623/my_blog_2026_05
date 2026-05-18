type PerfBeaconPayload = {
  path: string
  navigation_type?: string
  duration_ms?: number
  dcl_ms?: number
  load_ms?: number
  fcp_ms?: number
  lcp_ms?: number
}

let sent = false

const toFixedMs = (value: number | undefined) => {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0) return undefined
  return Math.round(value * 100) / 100
}

const postPerf = (payload: PerfBeaconPayload) => {
  const body = JSON.stringify(payload)
  const url = '/api/v1/system/perf/beacon'
  try {
    if (navigator.sendBeacon) {
      const blob = new Blob([body], { type: 'application/json' })
      navigator.sendBeacon(url, blob)
      return
    }
  } catch {
    // fallback below
  }

  void fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    keepalive: true,
    credentials: 'include',
  }).catch(() => {})
}

export const reportInitialPerf = () => {
  if (sent) return
  sent = true

  const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined
  const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0] as PerformanceEntry | undefined

  let lcpMs: number | undefined
  try {
    const observer = new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries()
      const last = entries[entries.length - 1]
      if (last) lcpMs = last.startTime
    })
    observer.observe({ type: 'largest-contentful-paint', buffered: true })
    setTimeout(() => observer.disconnect(), 3000)
  } catch {
    // ignore unsupported browsers
  }

  setTimeout(() => {
    const payload: PerfBeaconPayload = {
      path: window.location.pathname + window.location.search,
      navigation_type: navEntry?.type,
      duration_ms: toFixedMs(navEntry?.duration),
      dcl_ms: toFixedMs(navEntry ? navEntry.domContentLoadedEventEnd - navEntry.startTime : undefined),
      load_ms: toFixedMs(navEntry ? navEntry.loadEventEnd - navEntry.startTime : undefined),
      fcp_ms: toFixedMs(fcpEntry?.startTime),
      lcp_ms: toFixedMs(lcpMs),
    }
    postPerf(payload)
  }, 3200)
}
