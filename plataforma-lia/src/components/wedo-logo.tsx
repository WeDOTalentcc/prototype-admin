"use client"

interface WeDOLogoProps {
  className?: string
}

export function WeDOLogo({ className = "" }: WeDOLogoProps) {
  return (
    <span className={`font-bold tracking-tight ${className}`}>
      WeDO<span className="text-lia-text-secondary dark:text-lia-text-tertiary">Talent</span>
    </span>
  )
}
