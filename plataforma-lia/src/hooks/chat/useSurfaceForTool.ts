// src/hooks/chat/useSurfaceForTool.ts
import { SURFACE_CONFIG } from '@/lib/surface-config'

type ToolSurface = 'inline' | 'panel'

interface UseSurfaceOptions {
  isFullscreen: boolean
  itemCount?: number
}

/**
 * Resolve qual superfície usar para renderizar um tool result.
 *
 * @param toolName - Nome da tool (deve estar em SURFACE_CONFIG)
 * @param options.isFullscreen - true quando UnifiedChat está em mode="fullscreen"
 * @param options.itemCount - número de itens no resultado (para threshold dinâmico)
 * @returns 'inline' | 'panel'
 *
 * Regras em ordem de prioridade:
 * 1. Tool desconhecida → 'inline' (safe default, texto puro)
 * 2. hitl:true → 'inline' (aprovações nunca ficam no painel)
 * 3. !isFullscreen → 'inline' (painel não disponível)
 * 4. density_threshold definido E itemCount ≤ threshold → 'inline'
 * 5. config.default_surface
 */
export function useSurfaceForTool(
  toolName: string,
  options: UseSurfaceOptions
): ToolSurface {
  const { isFullscreen, itemCount } = options
  const config = SURFACE_CONFIG[toolName]

  if (!config) return 'inline'
  if (config.hitl) return 'inline'
  if (!isFullscreen) return 'inline'

  if (
    config.density_threshold !== undefined &&
    itemCount !== undefined &&
    itemCount <= config.density_threshold
  ) {
    return 'inline'
  }

  return config.default_surface as ToolSurface
}
