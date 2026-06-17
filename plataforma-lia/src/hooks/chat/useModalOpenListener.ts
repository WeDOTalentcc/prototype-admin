"use client"

import { useEffect, useState } from "react"

export interface ModalOpenEvent<T = Record<string, unknown>> {
  modal_id: string
  data: T
}

/**
 * Subscribes to `lia:open_modal` CustomEvent for a specific modal_id.
 *
 * Returns { isOpen, data, close }.
 * Dispatched by useUIAction when backend returns ui_action="open_modal".
 */
export function useModalOpenListener<T = Record<string, unknown>>(
  modal_id: string
) {
  const [isOpen, setIsOpen] = useState(false)
  const [data, setData] = useState<T>({} as T)

  useEffect(() => {
    function handleOpen(e: Event) {
      const detail = (e as CustomEvent<ModalOpenEvent<T>>).detail
      if (detail?.modal_id === modal_id) {
        setData(detail.data ?? ({} as T))
        setIsOpen(true)
      }
    }

    window.addEventListener("lia:open_modal", handleOpen)
    return () => window.removeEventListener("lia:open_modal", handleOpen)
  }, [modal_id])

  function close() {
    setIsOpen(false)
    setData({} as T)
  }

  return { isOpen, data, close }
}
