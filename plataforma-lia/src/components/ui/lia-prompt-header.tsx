"use client"

import React, { useEffect, useRef, useState } from "react"
import { Brain } from "lucide-react"

interface LiaPromptHeaderProps {
  title: string
  isAnimating?: boolean
}

const TYPING_SPEED = 36   // ms por caractere
const ERASE_SPEED  = 14   // ms por caractere apagando
const PAUSE_AFTER  = 9999 // ms antes de apagar (muito alto = nunca apaga no app real)

type Phase = "typing" | "done"

export const LiaPromptHeader = React.memo(function LiaPromptHeader({ title, isAnimating = false }: LiaPromptHeaderProps) {
  const [displayed, setDisplayed]     = useState("")
  const [phase, setPhase]             = useState<Phase>("typing")
  const [showCursor, setShowCursor]   = useState(true)
  const charRef   = useRef(0)
  const targetRef = useRef(title)

  // Cursor piscante independente
  useEffect(() => {
    const t = setInterval(() => setShowCursor(v => !v), 530)
    return () => clearInterval(t)
  }, [])

  // Reinicia typing quando title muda
  useEffect(() => {
    targetRef.current = title
    charRef.current   = 0
    setDisplayed("")
    setPhase("typing")
  }, [title])

  // Máquina de estados do typing
  useEffect(() => {
    const target = targetRef.current

    if (phase === "typing") {
      if (charRef.current < target.length) {
        const t = setTimeout(() => {
          charRef.current++
          setDisplayed(target.slice(0, charRef.current))
        }, TYPING_SPEED)
        return () => clearTimeout(t)
      } else {
        setPhase("done")
      }
    }
  }, [phase, displayed])

  // Cursor some 1.2s depois de terminar de digitar
  const cursorVisible = phase === "done"
    ? false          // cursor some quando termina
    : showCursor

  return (
    <div className="mb-4 flex flex-col items-center justify-center">
      <h2
        className={`text-xl font-semibold flex items-center gap-2 ${isAnimating ? 'animate-pulse' : ''}`}
      >
        <Brain className="w-7 h-7 text-wedo-cyan flex-shrink-0" strokeWidth={2} />
        <span>
          {displayed}
          <span
            style={{
              display: "inline-block",
              width: "2px",
              height: "1.1em",
              borderRadius: "2px",
              background: "var(--wedo-cyan, #60BED1)",
              opacity: cursorVisible ? 1 : 0,
              transition: "opacity 0.1s",
              verticalAlign: "middle",
              marginLeft: "1px",
              marginBottom: "1px",
            }}
          />
        </span>
      </h2>
    </div>
  )
})
LiaPromptHeader.displayName = 'LiaPromptHeader'
