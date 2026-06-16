"use client"

/**
 * OfferLinkCopyField — purely presentational copy-link field.
 * REGRA 6: zero hooks, zero fetch, only props + JSX.
 */
import { useState } from "react"
import { Copy, Check } from "lucide-react"

interface OfferLinkCopyFieldProps {
  link: string
}

export function OfferLinkCopyField({ link }: OfferLinkCopyFieldProps) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    navigator.clipboard.writeText(link).catch(() => {})
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-xs">
      <span className="flex-1 truncate font-mono text-green-800 select-all">{link}</span>
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? "Copiado!" : "Copiar link da proposta"}
        className="shrink-0 flex items-center gap-1 px-2 py-1 rounded bg-green-100 hover:bg-green-200 text-green-700 font-medium transition-colors"
      >
        {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
        {copied ? "Copiado" : "Copiar"}
      </button>
    </div>
  )
}
