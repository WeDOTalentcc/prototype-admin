import { Loader2 } from "lucide-react"

interface LoadingWatchdogOverlayProps {
  isVisible: boolean
  message?: string
}

export function LoadingWatchdogOverlay({
  isVisible,
  message = "Aguarde...",
}: LoadingWatchdogOverlayProps) {
  if (!isVisible) return null

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={message}
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/10 backdrop-blur-sm"
    >
      <div className="rounded-xl border border-lia-border-subtle bg-lia-bg-primary p-8 text-center shadow-md">
        <Loader2
          className="mx-auto mb-4 h-10 w-10 animate-spin motion-reduce:animate-none text-lia-text-secondary"
          aria-hidden="true"
        />
        <p className="text-sm text-lia-text-secondary">{message}</p>
      </div>
    </div>
  )
}
