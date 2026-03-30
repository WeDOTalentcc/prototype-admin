"use client"

/**
 * LiaChatButton — Botão flutuante fixo no canto inferior direito para abrir a LIA.
 *
 * Exibe ícone Brain (cyan, identidade LIA) flutuante sem background/borda.
 * Usa LiaFloatContext para estado global.
 *
 * Compatível com Vue: props onOpen mapeia para @click; estado via Pinia.
 */

import { Brain } from "lucide-react"
import { cn } from "@/lib/utils"
import { useLiaFloat } from "@/contexts/lia-float-context"

interface LiaChatButtonProps {
  className?: string
}

export function LiaChatButton({ className }: LiaChatButtonProps) {
  const { isOpen, toggle } = useLiaFloat()

  return (
    <button
      onClick={toggle}
      aria-label={isOpen ? "Fechar LIA" : "Abrir LIA"}
      title={isOpen ? "Fechar LIA" : "Conversar com LIA"}
      className={cn(
 "fixed bottom-6 right-6 z-50",
        "w-16 h-16",
        "flex items-center justify-center",
        "bg-transparent",
        "transition-colors duration-200",
        "hover:scale-110",
        "focus-visible:outline-none",
        className
      )}
    >
      <Brain
        className={cn(
 "w-10 h-10 transition-colors duration-200 drop-shadow-lia-md",
          isOpen
            ? "text-wedo-cyan scale-95"
            : "text-wedo-cyan hover:drop-shadow-lia-lg"
        )}
        strokeWidth={2}
      />
    </button>
  )
}
