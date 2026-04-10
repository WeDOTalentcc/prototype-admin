"use client"

import React, { useState } from "react"
import { ZoomIn } from "lucide-react"

interface Props {
  src: string
  caption?: string
  alt?: string
}

/**
 * ChatImageMessage — renders screenshot/image inline in chat messages.
 *
 * Used by LIA during tour to show screenshots of platform features.
 * Supports click-to-zoom.
 *
 * Integration: In UnifiedMessageList, check message.metadata.screenshot
 * and render this component.
 */
export function ChatImageMessage({ src, caption, alt }: Props) {
  const [zoomed, setZoomed] = useState(false)

  return (
    <>
      <div className="my-2 max-w-[280px]">
        <button
          onClick={() => setZoomed(true)}
          className="relative group rounded-lg overflow-hidden border border-lia-border-subtle hover:border-wedo-cyan/40 transition-colors"
        >
          <img
            src={src}
            alt={alt || caption || "Screenshot"}
            className="w-full h-auto rounded-lg"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
            <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>
        {caption && (
          <p className="text-[10px] text-lia-text-tertiary font-['Open_Sans',sans-serif] mt-1 px-1">
            {caption}
          </p>
        )}
      </div>

      {/* Zoom modal */}
      {zoomed && (
        <div
          className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-8"
          onClick={() => setZoomed(false)}
        >
          <img
            src={src}
            alt={alt || caption || "Screenshot"}
            className="max-w-full max-h-full rounded-lg shadow-2xl"
          />
        </div>
      )}
    </>
  )
}
