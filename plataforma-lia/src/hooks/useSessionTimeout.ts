import { useEffect, useCallback, useRef } from "react"
import { useRouter } from "next/navigation"

const SESSION_TIMEOUT_MS = 30 * 60 * 1000 // 30 minutos
const WARNING_BEFORE_MS = 2 * 60 * 1000   // aviso 2 min antes

interface UseSessionTimeoutOptions {
  onWarning?: () => void
  onTimeout?: () => void
  timeoutMs?: number
}

export function useSessionTimeout({
  onWarning,
  onTimeout,
  timeoutMs = SESSION_TIMEOUT_MS,
}: UseSessionTimeoutOptions = {}) {
  const router = useRouter()
  // @ts-ignore // TODO: fix type
  // @ts-ignore // TODO: fix type
  const timeoutRef = useRef<ReturnType<typeof setTimeout>>()
  // @ts-ignore // TODO: fix type
  const warningRef = useRef<ReturnType<typeof setTimeout>>()

  const resetTimer = useCallback(() => {
    clearTimeout(timeoutRef.current)
    clearTimeout(warningRef.current)

    warningRef.current = setTimeout(() => {
      onWarning?.()
    }, timeoutMs - WARNING_BEFORE_MS)

    timeoutRef.current = setTimeout(() => {
      onTimeout?.()
      router.push("/login?reason=session_expired")
    }, timeoutMs)
  }, [router, onWarning, onTimeout, timeoutMs])

  useEffect(() => {
    const events = ["mousedown", "keydown", "scroll", "touchstart", "click"]
    const handleActivity = () => resetTimer()
    events.forEach(event =>
      document.addEventListener(event, handleActivity, { passive: true })
    )
    resetTimer()
    return () => {
      events.forEach(event =>
        document.removeEventListener(event, handleActivity)
      )
      clearTimeout(timeoutRef.current)
      clearTimeout(warningRef.current)
    }
  }, [resetTimer])
}
