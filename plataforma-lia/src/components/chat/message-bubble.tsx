"use client"

import React, { useMemo } from "react"
import { User } from "lucide-react"
import { cn } from "@/lib/utils"
import { ActionResultCard } from "@/components/chat/action-result-card"
import { LIAIcon } from "@/components/ui/lia-icon"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"

interface MessageBubbleProps {
  sender: "lia" | "user"
  content: string
  timestamp: string
  actionResult?: {
    action_type: string
    result: Record<string, unknown>
  }
  userName?: string
  userAvatar?: string
  className?: string
}

function parseMarkdown(text: string): string {
  // Escape HTML entities FIRST to prevent XSS attacks
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
  
  // Escape the input first
  text = escapeHtml(text)

  const codeBlocks: string[] = []
  let processed = text.replace(/```([\s\S]*?)```/g, (_, code) => {
    codeBlocks.push(code.trim())
    return `%%CODEBLOCK_${codeBlocks.length - 1}%%`
  })

  processed = processed.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 rounded bg-gray-200 dark:bg-gray-700 text-[11px] font-mono text-gray-800 dark:text-gray-200">$1</code>')

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
        result.push('<ul class="list-disc pl-4 space-y-0.5">')
        inUl = true
      }
      result.push(`<li>${ulMatch[1]}</li>`)
    } else if (olMatch) {
      if (!inOl) {
        if (inUl) { result.push("</ul>"); inUl = false }
        result.push('<ol class="list-decimal pl-4 space-y-0.5">')
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
          1: "text-base font-semibold",
          2: "text-sm font-semibold",
          3: "text-[13px] font-medium",
        }
        result.push(`<div class="${sizes[level]} text-gray-900 dark:text-gray-50 mt-2 mb-1">${headerMatch[2]}</div>`)
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
    return `<pre class="rounded-md bg-gray-100 dark:bg-gray-900 p-3 my-2 overflow-x-auto"><code class="text-[11px] font-mono text-gray-800 dark:text-gray-200">${codeBlocks[parseInt(idx)]}</code></pre>`
  })

  return output
}

function RichTextContent({ html, className }: { html: string; className?: string }) {
  return (
    <div
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}

export function MessageBubble({
  sender,
  content,
  timestamp,
  actionResult,
  userName,
  userAvatar,
  className,
}: MessageBubbleProps) {
  const isLia = sender === "lia"

  const renderedContent = useMemo(() => {
    if (isLia) return parseMarkdown(content)
    return content.replace(/\n/g, "<br/>")
  }, [content, isLia])

  return (
    <div
      className={cn(
        "flex gap-3 animate-in fade-in duration-300",
        isLia ? "justify-start" : "justify-end",
        className
      )}
    >
      {isLia && (
        <div className="flex-shrink-0 mt-1">
          <LIAIcon size="sm" className="bg-cyan-50 dark:bg-cyan-900/20" />
        </div>
      )}

      <div
        className={cn(
          "max-w-[80%] rounded-md px-4 py-3",
          isLia
            ? "bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700"
            : "bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 ml-10"
        )}
      >
        <RichTextContent
          html={renderedContent}
          className={cn(
            "text-[13px] leading-relaxed font-['Open_Sans',sans-serif]",
            isLia
              ? "text-gray-800 dark:text-gray-200"
              : "text-gray-900 dark:text-gray-50"
          )}
        />

        {actionResult && (
          <ActionResultCard
            actionType={actionResult.action_type}
            result={actionResult.result}
            className="mt-2"
          />
        )}

        <div
          className={cn(
            "mt-2 text-[10px] font-['Inter',sans-serif] tabular-nums",
            isLia
              ? "text-gray-500 dark:text-gray-500"
              : "text-gray-400 dark:text-gray-500 text-right"
          )}
        >
          {timestamp}
        </div>
      </div>

      {!isLia && (
        <div className="flex-shrink-0 mt-1">
          <Avatar className="h-8 w-8">
            {userAvatar ? (
              <AvatarImage src={userAvatar} alt={userName || "User"} />
            ) : null}
            <AvatarFallback className="bg-gray-200 dark:bg-gray-600 text-gray-600 dark:text-gray-300 text-xs">
              {userName ? userName.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </AvatarFallback>
          </Avatar>
        </div>
      )}
    </div>
  )
}
