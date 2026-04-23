"use client"

import { useCallback } from "react"
import LiaLibraryPage from "@/components/pages/lia-library-page"

export function BibliotecaLiaRouteClient() {
  const handleNavigate = useCallback((page: string) => {
    window.dispatchEvent(new CustomEvent("lia:navigation-hint", { detail: { page, hint: "library" } }))
  }, [])
  return <LiaLibraryPage onNavigate={handleNavigate} />
}
