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

const IMAGE_URL_HINT_RE = /(?:\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?[^\s<>()]*)?|[?&](?:format|fmt|f)=(?:png|jpe?g|gif|webp|bmp|svg)\b[^\s<>()]*|[?&]fm=\d+\b[^\s<>()]*)/i
const htmlAnchorPattern = /<a\s+[^>]*href=(["'])(https?:\/\/[^"']+)\1[^>]*>([\s\S]*?)<\/a>/gi

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

const plainImageUrlLinePattern = /(^|\n)(\s*)(https?:\/\/[^\s<>()]+?\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?[^\s<>()]*)?)(?=\s*(?:\n|$))/gi
const markdownLinkImagePattern = /(?<!!)\[([^\]]*)\]\((https?:\/\/[^)\s]+?\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?[^)\s]*)?)\)/gi

const normalizePlainImageUrlLines = (markdown: string): string => {
  return markdown.replace(plainImageUrlLinePattern, (_match, prefix: string, indent: string, url: string) => {
    return `${prefix}${indent}![image](${url})`
  })
}

const normalizeMarkdownImageLinks = (markdown: string): string => {
  return markdown.replace(markdownLinkImagePattern, (_match, altText: string, url: string) => {
    const safeAltText = altText || 'image'
    return `![${safeAltText}](${url})`
  })
}

const htmlImageAnchorPattern = /<a\s+[^>]*href=(["'])(https?:\/\/[^"']+?\.(?:png|jpe?g|gif|webp|bmp|svg)(?:\?[^"']*)?)\1[^>]*>([\s\S]*?)<\/a>/gi

const normalizeHtmlImageAnchors = (markdown: string): string => {
  return markdown.replace(htmlImageAnchorPattern, (_match, _quote: string, href: string, innerHtml: string) => {
    const trimmedInner = innerHtml.trim()
    const altText = trimmedInner.replace(/<[^>]+>/g, '').trim() || 'image'
    return `![${altText}](${href})`
  })
}

const decodeHtmlEntities = (value: string): string => {
  return value.replace(/&amp;/gi, '&')
}

const isImageLikeUrl = (url: string): boolean => {
  const decoded = decodeHtmlEntities(url)
  return IMAGE_URL_HINT_RE.test(decoded)
}

const normalizeRenderedHtmlImageAnchors = (html: string): string => {
  return html.replace(htmlAnchorPattern, (match, _quote: string, href: string, innerHtml: string) => {
    const normalizedHref = decodeHtmlEntities(href)
    if (!isImageLikeUrl(normalizedHref)) return match
    if (/<img\b/i.test(innerHtml)) return match

    const plainText = innerHtml.replace(/<[^>]+>/g, '').trim()
    const safeAlt = md.utils.escapeHtml(plainText || 'image')
    const safeSrc = md.utils.escapeHtml(normalizedHref)
    return `<img src="${safeSrc}" alt="${safeAlt}" loading="lazy" decoding="async" />`
  })
}

export const useMarkdown = () => {
  const htmlContent = ref('')

  const render = (content: string): string => {
    try {
      const normalized = normalizePlainImageUrlLines(
        normalizeMarkdownImageLinks(
          normalizeHtmlImageAnchors(content)
        )
      )
      const html = md.render(normalized)
      return normalizeRenderedHtmlImageAnchors(html)
    } catch (error) {
      console.error('Markdown 渲染失败:', error)
      return '<p>渲染失败</p>'
    }
  }

  const renderToRef = (markdown: string) => {
    htmlContent.value = render(markdown)
  }

  return {
    htmlContent,
    render,
    renderToRef,
  }
}
