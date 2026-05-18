import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

const parseAllowedHosts = (...sources: Array<string | undefined>) => {
  const cleaned = new Set<string>()

  for (const source of sources) {
    if (!source) continue
    for (const rawHost of source.split(',')) {
      const host = rawHost
        .trim()
        .replace(/^https?:\/\//, '')
        .replace(/\/.*$/, '')
      if (!host) continue
      cleaned.add(host)
    }
  }

  // Fallback for cloudflared domains used in this project.
  if (cleaned.size === 0) {
    cleaned.add('dreamrage.one')
    cleaned.add('www.dreamrage.one')
    cleaned.add('.dreamrage.one')
  }

  return Array.from(cleaned)
}

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const rootEnvDir = resolve(__dirname, '..')
  const rootEnv = loadEnv(mode, rootEnvDir, '')
  const frontendEnv = loadEnv(mode, __dirname, '')
  const allowedHosts = parseAllowedHosts(
    frontendEnv.VITE_ALLOWED_HOSTS,
    rootEnv.VITE_ALLOWED_HOSTS,
    process.env.VITE_ALLOWED_HOSTS
  )

  return {
    plugins: [vue(), tailwindcss()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
      },
    },
    server: {
      port: 5173,
      allowedHosts,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          ws: true,
          timeout: 60000,
          proxyTimeout: 60000,
          configure: (proxy) => {
            proxy.on('error', (err, _req, res) => {
              console.warn('[vite proxy /api error]', err.message)
              if (res && typeof (res as any).writeHead === 'function') {
                ;(res as any).writeHead(502, { 'Content-Type': 'text/plain' })
                ;(res as any).end('Proxy error: ' + err.message)
              }
            })
          },
        },
        '/ws': {
          target: 'ws://127.0.0.1:8000',
          ws: true,
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: false,
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('echarts') || id.includes('vue-echarts')) {
                return 'echarts'
              }
              if (id.includes('markdown-it') || id.includes('highlight.js')) {
                return 'markdown'
              }
              if (id.includes('lucide-vue-next')) {
                return 'icons'
              }
            }
          },
        },
      },
    },
  }
})
