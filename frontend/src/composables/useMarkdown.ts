import { ref } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

// 创建 markdown-it 实例
const md: MarkdownIt = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight: (str: string, lang: string): string => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang }).value}</code></pre>`
      } catch (error) {
        console.error('代码高亮失败:', error)
      }
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

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
