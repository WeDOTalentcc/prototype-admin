import { useState } from "react"

export function useJobPreviewState() {
  const [expandedBlocks, setExpandedBlocks] = useState<number[]>([0, 1, 2, 3, 4, 6])
  const [collapsedPreviewSections, setCollapsedPreviewSections] = useState<string[]>([])

  const togglePreviewSection = (section: string) => {
    setCollapsedPreviewSections(prev =>
      prev.includes(section) ? prev.filter(s => s !== section) : [...prev, section]
    )
  }

  const toggleBlock = (blockId: number) => {
    setExpandedBlocks(prev =>
      prev.includes(blockId) ? prev.filter(id => id !== blockId) : [...prev, blockId]
    )
  }

  return {
    expandedBlocks,
    collapsedPreviewSections,
    togglePreviewSection,
    toggleBlock,
  }
}
