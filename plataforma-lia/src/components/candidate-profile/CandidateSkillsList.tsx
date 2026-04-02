"use client"

import React, { memo } from "react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface CandidateSkillsListProps {
  skills: string[]
  maxVisible?: number
  size?: "sm" | "md"
  className?: string
  onOverflowClick?: () => void
}

const CandidateSkillsList = memo(function CandidateSkillsList({
  skills,
  maxVisible = 5,
  size = "sm",
  className,
  onOverflowClick,
}: CandidateSkillsListProps) {
  if (!skills || skills.length === 0) return null

  const visible = skills.slice(0, maxVisible)
  const overflowCount = skills.length - maxVisible

  return (
    <div className={cn("flex flex-wrap gap-1", className)}>
      {visible.map((skill) => (
        <Badge
          key={skill}
          variant="secondary"
          className={cn(
            "border-0 bg-lia-bg-tertiary text-lia-text-primary dark:bg-lia-bg-secondary dark:text-lia-text-primary",
            size === "sm" ? "text-micro px-1.5 py-0" : "text-xs px-2 py-0.5"
          )}
        >
          {skill}
        </Badge>
      ))}
      {overflowCount > 0 && (
        <button
          type="button"
          onClick={onOverflowClick}
          className={cn(
            "text-lia-text-secondary hover:text-lia-text-primary transition-colors",
            size === "sm" ? "text-micro" : "text-xs"
          )}
        >
          +{overflowCount}
        </button>
      )}
    </div>
  )
})

CandidateSkillsList.displayName = "CandidateSkillsList"

export { CandidateSkillsList }
export type { CandidateSkillsListProps }
