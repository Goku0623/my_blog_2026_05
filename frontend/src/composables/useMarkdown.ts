import { ref } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import typescript from 'highlight.js/lib/languages/typescript'
import json from 'highlight.js/lib/languages/json'
import bash from 'highlight.js/lib/languages/bash'
import python from 'highlight.js/lib/languages/python'
import xml from 'highlight.js/lib/languages/xml'

hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('python', python)
hljs.registerLanguage('xml', xml)

const LANGUAGE_ALIAS_MAP: Record<string, string> = {
  js: 'javascript',
  ts: 'typescript',
  sh: 'bash',
  shell: 'bash',
  py: 'python',
  html: 'xml',
}

// 创建 markdown-it 实例
const md: MarkdownIt = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string): string => {
    const normalizedLang = (LANGUAGE_ALIAS_MAP[lang?.toLowerCase()] ?? lang?.toLowerCase()) || ''
    if (normalizedLang && hljs.getLanguage(normalizedLang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: normalizedLang }).value}</code></pre>`
      } catch (error) {
        console.error('代码高亮失败:', error)
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

const defaultImageRenderer = md.renderer.rules.image
md.renderer.rules.image = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  token.attrSet('loading', 'lazy')
  token.attrSet('decoding', 'async')
  if (defaultImageRenderer) {
    return defaultImageRenderer(tokens, idx, options, env, self)
  }
  return self.renderToken(tokens, idx, options)
}

export const useMarkdown = () => {
  const htmlContent = ref('')

  // 渲染 Markdown 为 HTML
  const render = (markdown: string): string => {
    try {
      return md.render(markdown)
    } catch (error) {
      console.error('Markdown 渲染失败:', error)
      return '<p>渲染失败</p>'
    }
  }

  // 渲染 Markdown 并存储到 ref
  const renderToRef = (markdown: string) => {
    htmlContent.value = render(markdown)
  }

  return {
    htmlContent,
    render,
    renderToRef,
  }
}
