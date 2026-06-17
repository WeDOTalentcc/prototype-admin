import { marked } from "marked"
import { sanitizeHtml } from "./sanitize"

marked.setOptions({
  breaks: true,
  gfm: true,
})

export function renderMarkdown(raw: string): string {
  if (!raw) return ""
  const html = marked.parse(raw, { async: false }) as string
  return sanitizeHtml(html)
}
