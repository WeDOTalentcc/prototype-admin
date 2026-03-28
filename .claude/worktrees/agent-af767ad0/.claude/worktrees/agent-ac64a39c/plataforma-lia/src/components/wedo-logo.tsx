"use client"

interface WeDOLogoProps {
  className?: string
}

export function WeDOLogo({ className = "" }: WeDOLogoProps) {
  return (
    <span className={`font-bold tracking-tight ${className}`}>
      WeDO<span className="text-gray-600 dark:text-gray-400">Talent</span>
    </span>
  )
}
