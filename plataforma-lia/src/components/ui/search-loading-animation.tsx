'use client'

import React from "react"
import { Search, Check } from 'lucide-react'

interface SearchLoadingAnimationProps {
  isActive: boolean
}

const pingStyle: React.CSSProperties = {
  animation: 'ping-custom 1s cubic-bezier(0, 0, 0.2, 1) infinite',
}
const pulseStyle: React.CSSProperties = {
  animation: 'pulse-custom 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
}
const spinStyle: React.CSSProperties = {
  animation: 'spin-custom 1s linear infinite',
}

export const SearchLoadingAnimation = React.memo(function SearchLoadingAnimation({ isActive }: SearchLoadingAnimationProps) {
  if (!isActive) return null

  return (
    <div
      className="mb-6 p-4 rounded-xl bg-lia-bg-primary max-w-md border-l-[3px] border-l-lia-border-default"
    >
      <style>{`
        @keyframes ping-custom {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
        @keyframes pulse-custom {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        @keyframes spin-custom {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      <div className="flex items-center gap-3 mb-3">
        <div className="relative flex items-center justify-center w-12 h-12">
          <div
            style={pingStyle}
            className="absolute w-10 h-10 rounded-full bg-wedo-cyan/40"
          />
          <div
            style={pulseStyle}
            className="relative w-10 h-10 rounded-full flex items-center justify-center z-10 bg-wedo-cyan/20"
          >
            <Search className="w-5 h-5 text-lia-text-secondary" />
          </div>
        </div>
        <div className="text-left">
          <p className="text-sm font-semibold text-lia-text-primary">
            Processando busca...
          </p>
          <p className="text-xs text-lia-text-secondary">
            Analisando critérios e perfis
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
          <div className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 bg-wedo-green">
            <Check className="w-2.5 h-2.5 text-white" strokeWidth={3} />
          </div>
          <span>Interpretando</span>
        </div>
        <span className="lia-text-secondary text-xs">•</span>
        <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
          <div
            style={spinStyle}
            className="w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 bg-lia-text-primary"
          >
            <div className="w-2 h-2 border-2 border-white border-t-transparent rounded-full" />
          </div>
          <span>Buscando</span>
        </div>
        <span className="lia-text-secondary text-xs">•</span>
        <div className="flex items-center gap-1.5 text-xs text-lia-text-secondary">
          <div className="w-4 h-4 rounded-full bg-lia-interactive-active flex-shrink-0" />
          <span>Rankeando</span>
        </div>
      </div>
    </div>
  )
})
SearchLoadingAnimation.displayName = 'SearchLoadingAnimation'
