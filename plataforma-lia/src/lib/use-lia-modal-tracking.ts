/**
 * useLiaModalTracking — canonical guide for modal context awareness (P0-2, 2026-06-18).
 *
 * Call this hook ONCE inside any modal component to automatically notify
 * LIA about which modal is open when the recruiter sends a chat message.
 *
 * Rules of Hooks: place as the FIRST statement in the component function body.
 *
 * Pattern:
 *   export function MyModal({ isOpen, ... }: Props) {
 *     useLiaModalTracking('my-modal', isOpen)   ← first line
 *     ...
 *   }
 *
 * Sensor: scripts/check_modal_lia_context.mjs detects Dialog components
 * that don't import this hook (or setLiaModal directly).
 */
import { useEffect } from 'react'
import { setLiaModal } from './lia-context-store'

/**
 * Wire modal open/close into LIA screen state.
 * @param name  Stable identifier shown in the LIA system prompt (e.g. 'send-email')
 * @param isOpen Whether the modal is currently open
 */
export function useLiaModalTracking(name: string, isOpen: boolean): void {
  useEffect(() => {
    if (isOpen) setLiaModal(name)
    // Cleanup: clear modal name when this instance unmounts or isOpen becomes false
    return () => setLiaModal(null)
  }, [name, isOpen])
}
