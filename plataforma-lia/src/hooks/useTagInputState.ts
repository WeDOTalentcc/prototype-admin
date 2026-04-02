"use client"

import { useState, useRef, useEffect, useCallback } from "react"

/**
 * Shared state and behavior for all semantic tag inputs
 * (SkillsFilterInput, ExpertiseAreasInput, ExcludedCompaniesInput, etc.)
 *
 * Extracts: input state, dropdown open/close, keyboard navigation, click-outside detection.
 * Each consuming component keeps its own domain logic (AI endpoints, badge rendering, item types).
 */
export function useTagInputState() {
  const [inputValue, setInputValue] = useState("")
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current && !dropdownRef.current.contains(event.target as Node) &&
        inputRef.current && !inputRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false)
        setFocusedIndex(-1)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const handleKeyNavigation = useCallback((
    e: React.KeyboardEvent,
    itemCount: number,
    onSelectFocused: (index: number) => void,
    onEnterEmpty: () => void
  ) => {
    if (e.key === "Enter") {
      e.preventDefault()
      if (focusedIndex >= 0 && focusedIndex < itemCount) {
        onSelectFocused(focusedIndex)
      } else {
        onEnterEmpty()
      }
    } else if (e.key === "ArrowDown") {
      e.preventDefault()
      setFocusedIndex(prev => Math.min(prev + 1, itemCount - 1))
    } else if (e.key === "ArrowUp") {
      e.preventDefault()
      setFocusedIndex(prev => Math.max(prev - 1, -1))
    } else if (e.key === "Escape") {
      setIsDropdownOpen(false)
      setFocusedIndex(-1)
    }
  }, [focusedIndex])

  const closeDropdown = useCallback(() => {
    setIsDropdownOpen(false)
    setFocusedIndex(-1)
  }, [])

  const openDropdown = useCallback(() => {
    setIsDropdownOpen(true)
    setFocusedIndex(-1)
  }, [])

  return {
    inputValue,
    setInputValue,
    isDropdownOpen,
    setIsDropdownOpen,
    focusedIndex,
    setFocusedIndex,
    inputRef,
    dropdownRef,
    handleKeyNavigation,
    closeDropdown,
    openDropdown,
  }
}
