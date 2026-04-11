"use client"

/**
 * useTemplateSend — placeholder for future template-sending logic.
 *
 * Currently the original hook did not contain explicit send/mutation logic
 * (sending is handled elsewhere). This module exists as a seam for future
 * send-related functionality (e.g. optimistic updates, send-tracking state).
 *
 * Re-exported through the facade for forward-compatibility.
 */

export interface UseTemplateSendReturn {
  /** Reserved for future send state */
  isSending: boolean
}

export function useTemplateSend(): UseTemplateSendReturn {
  return {
    isSending: false,
  }
}
