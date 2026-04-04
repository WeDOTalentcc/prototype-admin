"use client"

import { usePathname } from "next/navigation"
import { LiaChatButton } from "./LiaChatButton"
import { LiaChatPanel } from "./LiaChatPanel"
import { LiaSuperPrompt } from "./LiaSuperPrompt"
import { useLiaFloat } from "@/contexts/lia-float-context"

const HIDDEN_PATHS = ["/login", "/login/welcome", "/forgot-password", "/reset-password"]

export function LiaFloatConditional() {
  const pathname = usePathname()
  const { splitView } = useLiaFloat()
  const isHidden = HIDDEN_PATHS.some((p) => pathname === p || pathname.startsWith(p + "/"))
  if (isHidden) return null
  return (
    <>
      <LiaChatPanel />
      <LiaChatButton />
      {!splitView.active && <LiaSuperPrompt />}
    </>
  )
}
