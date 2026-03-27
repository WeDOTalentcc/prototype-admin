export function escapeHtml(str: string): string {
  const map: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }
  return str.replace(/[&<>"']/g, (char) => map[char])
}

export function cleanAgentResponse(raw: string): string {
  let text = raw

  const jsonBlockRe = /```json\s*\{[\s\S]*?\}\s*```/g
  text = text.replace(jsonBlockRe, '')

  const rawJsonRe = /\{\s*"thought"\s*:[\s\S]*?"response"\s*:\s*(?:null|"[^"]*")\s*\}/g
  text = text.replace(rawJsonRe, '')

  const responseMatch = text.match(/"response"\s*:\s*"((?:[^"\\]|\\.)*)"/s)
  if (responseMatch && text.trim().startsWith('{')) {
    try {
      text = JSON.parse(`"${responseMatch[1]}"`)
    } catch {
      text = responseMatch[1]
    }
  }

  text = text.replace(/^\s*[\n\r]+/, '').replace(/[\n\r]+\s*$/, '')

  return text || raw
}

export function parseChatMarkdown(text: string): string {
  const escapeHtml = (str: string): string => {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;'
    }
    return str.replace(/[&<>"']/g, (char) => map[char])
  }

  text = escapeHtml(text)

  const codeBlocks: string[] = []
  let processed = text.replace(/```([\s\S]*?)```/g, (_, code) => {
    codeBlocks.push(code.trim())
    return `%%CODEBLOCK_${codeBlocks.length - 1}%%`
  })

  processed = processed.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-xs font-mono text-gray-800 dark:text-gray-200">$1</code>')
  processed = processed.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
  processed = processed.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>")

  const lines = processed.split("\n")
  const result: string[] = []
  let inUl = false
  let inOl = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const ulMatch = line.match(/^[-•]\s+(.+)/)
    const olMatch = line.match(/^\d+\.\s+(.+)/)

    if (ulMatch) {
      if (!inUl) {
        if (inOl) { result.push("</ol>"); inOl = false }
        result.push('<ul class="list-disc pl-4 space-y-0.5 my-1">')
        inUl = true
      }
      result.push(`<li>${ulMatch[1]}</li>`)
    } else if (olMatch) {
      if (!inOl) {
        if (inUl) { result.push("</ul>"); inUl = false }
        result.push('<ol class="list-decimal pl-4 space-y-0.5 my-1">')
        inOl = true
      }
      result.push(`<li>${olMatch[1]}</li>`)
    } else {
      if (inUl) { result.push("</ul>"); inUl = false }
      if (inOl) { result.push("</ol>"); inOl = false }

      const headerMatch = line.match(/^(#{1,3})\s+(.+)/)
      if (headerMatch) {
        const level = headerMatch[1].length
        const sizes: Record<number, string> = {
          1: "text-base-ui font-semibold",
          2: "text-sm-ui font-semibold",
          3: "text-sm-ui font-medium",
        }
        result.push(`<div class="${sizes[level]} text-gray-900 dark:text-gray-50 mt-2 mb-1">${headerMatch[2]}</div>`)
      } else if (line.trim() === "---" || line.trim() === "___") {
        result.push('<hr class="my-2 border-gray-200 dark:border-gray-700"/>')
      } else if (line.trim() === "") {
        result.push("<br/>")
      } else {
        result.push(`<span>${line}</span><br/>`)
      }
    }
  }
  if (inUl) result.push("</ul>")
  if (inOl) result.push("</ol>")

  let output = result.join("")

  output = output.replace(/%%CODEBLOCK_(\d+)%%/g, (_, idx) => {
    return `<pre class="rounded-md bg-gray-100 dark:bg-gray-900 p-2 my-1.5 overflow-x-auto"><code class="text-micro font-mono text-gray-800 dark:text-gray-200">${codeBlocks[parseInt(idx)]}</code></pre>`
  })

  output = output.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, href) => {
    const isInternal = href.startsWith("/")
    const isSafeProtocol = /^(https?:\/\/|\/)/i.test(href)
    if (!isSafeProtocol) return label
    return `<a href="${href}" ${isInternal ? '' : 'target="_blank" rel="noopener noreferrer"'} class="text-wedo-cyan underline hover:opacity-80 transition-opacity">${label}</a>`
  })

  return output
}
