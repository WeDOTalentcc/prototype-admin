"use client"

import React, { useState, useEffect, useRef, useCallback } from "react"
import { useRouter, usePathname } from "next/navigation"
import { AlertCircle, Settings, GripVertical } from "lucide-react"

const AUTH_PAGES = ['/login', '/forgot-password', '/reset-password', '/register', '/accept-invitation']
const ADMIN_PREFIX = '/admin'

interface SettingsProgress {
  overall: number
  sections: Record<string, number>
  subsections: Record<string, boolean>
}

const DEFAULT_PROGRESS: SettingsProgress = {
  overall: 50,
  sections: {
    'company-team': 60,
    'recruitment': 40,
    'communication': 60,
    'goals-planning': 50,
    'global-search': 80
  },
  subsections: {}
}

const STORAGE_KEY = 'setup-badge-position'

export function SetupAlertBadge() {
  const router = useRouter()
  const pathname = usePathname()
  const badgeRef = useRef<HTMLButtonElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [progress, setProgress] = useState<SettingsProgress>(DEFAULT_PROGRESS)
  const [isLoading, setIsLoading] = useState(true)
  const dragOffset = useRef({ x: 0, y: 0 })

  const isAuthPage = AUTH_PAGES.some(page => pathname?.startsWith(page))
  const isAdminPage = pathname?.startsWith(ADMIN_PREFIX)

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const response = await fetch('/api/backend-proxy/settings/progress')
        if (response.ok) {
          const data = await response.json()
          setProgress(data)
        }
      } catch (error) {
        console.error('Failed to fetch settings progress:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchProgress()
    const interval = setInterval(fetchProgress, 60000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setPosition(parsed)
      } catch {
        setPosition({ x: window.innerWidth - 220, y: window.innerHeight - 70 })
      }
    } else {
      setPosition({ x: window.innerWidth - 220, y: window.innerHeight - 70 })
    }
  }, [])

  useEffect(() => {
    if (position.x !== 0 || position.y !== 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(position))
    }
  }, [position])

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (badgeRef.current) {
      const rect = badgeRef.current.getBoundingClientRect()
      dragOffset.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
      setIsDragging(true)
      e.preventDefault()
    }
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isDragging) {
      const newX = Math.max(0, Math.min(window.innerWidth - 200, e.clientX - dragOffset.current.x))
      const newY = Math.max(0, Math.min(window.innerHeight - 60, e.clientY - dragOffset.current.y))
      setPosition({ x: newX, y: newY })
    }
  }, [isDragging])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
  }, [])

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, handleMouseMove, handleMouseUp])

  const overallCompletion = progress.overall

  if (isLoading || overallCompletion >= 100 || isAuthPage || isAdminPage) {
    return null
  }

  const handleClick = () => {
    if (!isDragging) {
      router.push('/configuracoes')
    }
  }

  const getProgressColor = () => {
    if (overallCompletion >= 80) return '#374151'
    if (overallCompletion >= 50) return '#4BA8BA'
    return '#F59E0B'
  }

  return (
    <button
      ref={badgeRef}
      onClick={handleClick}
      className="fixed z-50 flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl hover:transition-shadow duration-200 font-sans select-none"
      style={{ 
        fontFamily: 'var(--font-open-sans), Open Sans, sans-serif',
        left: `${position.x}px`,
        top: `${position.y}px`,
        cursor: isDragging ? 'grabbing' : 'pointer'
      }}
      title="Clique para completar o setup da empresa. Arraste para reposicionar."
    >
      <div 
        onMouseDown={handleMouseDown}
        className="cursor-grab active:cursor-grabbing p-0.5 -ml-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
        title="Arraste para mover"
      >
        <GripVertical className="w-3 h-3 text-gray-400" />
      </div>
      <div className="relative">
        <div 
          className="w-8 h-8 rounded-md flex items-center justify-center"
          style={{ backgroundColor: `${getProgressColor()}20` }}
        >
          <AlertCircle 
            className="w-4 h-4" 
            style={{ color: getProgressColor() }}
          />
        </div>
        <div 
          className="absolute -top-1 -right-1 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
          style={{ backgroundColor: getProgressColor() }}
        >
          !
        </div>
      </div>
      <div className="flex flex-col items-start">
        <span className="text-[10px] font-medium text-gray-500 dark:text-gray-400 leading-tight">
          Setup Incompleto
        </span>
        <div className="flex items-center gap-1.5">
          <span 
            className="text-xs font-semibold leading-tight"
            style={{ color: getProgressColor() }}
          >
            {overallCompletion}%
          </span>
          <div className="w-12 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full rounded-full transition-all duration-300"
              style={{ 
                width: `${overallCompletion}%`,
                backgroundColor: getProgressColor()
              }}
            />
          </div>
        </div>
      </div>
      <Settings className="w-3 h-3 text-gray-400 ml-1" />
    </button>
  )
}
