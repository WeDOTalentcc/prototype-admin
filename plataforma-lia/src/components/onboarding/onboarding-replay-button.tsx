"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator
} from "@/components/ui/dropdown-menu"
import { useAiPersona } from "@/hooks/company/use-ai-persona"
import {
  BookOpen, HelpCircle,
  Video, FileText, Heart
} from "lucide-react"

interface OnboardingReplayButtonProps {
  variant?: 'button' | 'dropdown' | 'minimal'
  className?: string
}

export function OnboardingReplayButton({
  variant = 'dropdown',
  className = ""
}: OnboardingReplayButtonProps) {
  const { persona } = useAiPersona()
  const personaName = persona?.name ?? "IA"
  const [isHovered, setIsHovered] = useState(false)

  if (variant === 'minimal' || variant === 'button') {
    return (
      <Button
        variant="ghost"
        size="sm"
        className={`gap-2 ${className}`}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={() => window.open('/', '_self')}
      >
        <div
          className="transition-transform motion-reduce:transition-none duration-300"
          style={{transform: isHovered ? 'rotate(360deg)' : 'rotate(0deg)'}}
        >
          <HelpCircle className="w-4 h-4" />
        </div>
        Ajuda
      </Button>
    )
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className={`gap-2 ${className}`}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <div
            className="transition-transform motion-reduce:transition-none duration-200"
            style={{transform: isHovered ? 'scale(1.1)' : 'scale(1)'}}
          >
            <HelpCircle className="w-4 h-4" />
          </div>
          Ajuda
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuItem className="gap-3 cursor-pointer">
          <div className="w-8 h-8 bg-status-success/15 rounded-md flex items-center justify-center">
            <BookOpen className="w-4 h-4 text-status-success" />
          </div>
          <div className="flex-1">
            <div className="font-medium">Central de Ajuda</div>
            <div className="text-xs text-lia-text-primary">
              Documentação e tutoriais
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem className="gap-3 cursor-pointer">
          <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl flex items-center justify-center">
            <Video className="w-4 h-4 text-wedo-purple" />
          </div>
          <div className="flex-1">
            <div className="font-medium">Vídeos Tutoriais</div>
            <div className="text-xs text-lia-text-primary">
              Aprenda com exemplos práticos
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuItem className="gap-3 cursor-pointer">
          <div className="w-8 h-8 bg-wedo-orange/15 rounded-md flex items-center justify-center">
            <FileText className="w-4 h-4 text-wedo-orange" />
          </div>
          <div className="flex-1">
            <div className="font-medium">Guia de Início Rápido</div>
            <div className="text-xs text-lia-text-primary">
              Setup em 3 passos simples
            </div>
          </div>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem className="gap-3 cursor-pointer">
          <div className="w-8 h-8 bg-wedo-magenta/15 rounded-md flex items-center justify-center">
            <Heart className="w-4 h-4 text-wedo-magenta" />
          </div>
          <div className="flex-1">
            <div className="font-medium">Feedback</div>
            <div className="text-xs text-lia-text-primary">
              {`Ajude-nos a melhorar ${personaName}`}
            </div>
          </div>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
