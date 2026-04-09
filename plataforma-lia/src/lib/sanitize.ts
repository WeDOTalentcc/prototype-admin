import DOMPurify from "dompurify"

/**
 * Sanitiza HTML para uso seguro em dangerouslySetInnerHTML
 * Previne XSS — use em TODOS os pontos que renderizam HTML de fontes externas
 */
export function sanitizeHtml(dirty: string): string {
  if (typeof window === "undefined") {
    // SSR: retorna string sem tags (server-side não tem DOM)
    return dirty.replace(/<[^>]*>/g, "")
  }
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "br", "p", "ul", "ol", "li", "span", "code", "pre",
                   "h1", "h2", "h3", "h4", "h5", "h6", "table", "thead", "tbody", "tr", "th", "td",
                   "blockquote", "hr", "del", "input"],
    ALLOWED_ATTR: ["href", "target", "rel", "class", "type", "checked", "disabled"],
    ADD_ATTR: ["target"],
  })
}

/**
 * Versão permissiva para templates de email (mais tags permitidas)
 */
export function sanitizeEmailHtml(dirty: string): string {
  if (typeof window === "undefined") {
    return dirty.replace(/<[^>]*>/g, "")
  }
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "br", "p", "ul", "ol", "li",
                   "span", "div", "h1", "h2", "h3", "h4", "table", "tr", "td",
                   "th", "thead", "tbody", "img", "code", "pre", "blockquote"],
    ALLOWED_ATTR: ["href", "target", "rel", "class", "style", "src", "alt", "width", "height"],
  })
}
