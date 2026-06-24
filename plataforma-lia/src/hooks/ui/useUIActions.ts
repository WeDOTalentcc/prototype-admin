/**
 * @deprecated Pre-unified-chat hook. Zero external callers.
 * Canonical: useLiaPanelStore (wizard panel focus) + openDynamicPanel (panel content).
 * This file may be removed in a future cleanup sprint.
 */
"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { UIAction, SidePanelType, PanelSubmitData, ChatCardType } from "@/components/ui-actions/types"

interface UIActionsState {
  activePanelType: SidePanelType | null
  activePanelData: Record<string, unknown>
  activePanelTitle: string
  isLoading: boolean
  pendingActions: UIAction[]
  connectionStatus: "connecting" | "connected" | "disconnected" | "error"
}

interface UseUIActionsOptions {
  conversationId?: string
  onPanelSubmit?: (data: PanelSubmitData) => Promise<void>
  onPanelClose?: (panelType: SidePanelType) => void
  onChatCardAction?: (cardType: ChatCardType, action: string, data: unknown) => void
  websocketUrl?: string
  enableWebSocket?: boolean
}

const MAX_RECONNECT_ATTEMPTS = 5
const BASE_RECONNECT_DELAY = 1000

export function useUIActions(options: UseUIActionsOptions = {}) {
  const { 
    conversationId, 
    onPanelSubmit, 
    onPanelClose, 
    onChatCardAction,
    websocketUrl,
    enableWebSocket = true
  } = options
  
  const [state, setState] = useState<UIActionsState>({
    activePanelType: null,
    activePanelData: {},
    activePanelTitle: "",
    isLoading: false,
    pendingActions: [],
    connectionStatus: "disconnected"
  })
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptRef = useRef(0)
  const isMountedRef = useRef(true)

  const openPanel = useCallback((
    panelType: SidePanelType, 
    data: Record<string, unknown> = {},
    title: string = ""
  ) => {
    setState(prev => ({
      ...prev,
      activePanelType: panelType,
      activePanelData: data,
      activePanelTitle: title
    }))
  }, [])

  const closePanel = useCallback(() => {
    const currentPanelType = state.activePanelType
    setState(prev => ({
      ...prev,
      activePanelType: null,
      activePanelData: {},
      activePanelTitle: ""
    }))
    if (currentPanelType && onPanelClose) {
      onPanelClose(currentPanelType)
    }
  }, [state.activePanelType, onPanelClose])

  const submitPanel = useCallback(async (data: PanelSubmitData) => {
    setState(prev => ({ ...prev, isLoading: true }))
    try {
      if (onPanelSubmit) {
        await onPanelSubmit(data)
      }
      closePanel()
    } catch (error) {
      throw error
    } finally {
      setState(prev => ({ ...prev, isLoading: false }))
    }
  }, [onPanelSubmit, closePanel])

  const handleUIAction = useCallback((action: UIAction) => {
    if (action.component_type === "side_panel") {
      openPanel(
        action.component_subtype as SidePanelType,
        action.data,
        action.title
      )
    } else if (action.component_type === "notification") {
      setState(prev => ({
        ...prev,
        pendingActions: [...prev.pendingActions, action]
      }))
    } else if (action.component_type === "chat_card") {
      setState(prev => ({
        ...prev,
        pendingActions: [...prev.pendingActions, action]
      }))
    }
  }, [openPanel])

  const handleChatCardAction = useCallback((cardType: ChatCardType, action: string, data: unknown) => {
    if (onChatCardAction) {
      onChatCardAction(cardType, action, data)
    }
  }, [onChatCardAction])

  const dismissAction = useCallback((actionId: string) => {
    setState(prev => ({
      ...prev,
      pendingActions: prev.pendingActions.filter(a => a.action_id !== actionId)
    }))
  }, [])

  const clearPendingActions = useCallback(() => {
    setState(prev => ({
      ...prev,
      pendingActions: []
    }))
  }, [])

  useEffect(() => {
    isMountedRef.current = true
    
    if (typeof window === 'undefined') return
    if (!enableWebSocket || !websocketUrl || !conversationId) return

    const connectWebSocket = () => {
      if (!isMountedRef.current) return
      
      setState(prev => ({ ...prev, connectionStatus: "connecting" }))
      
      try {
        const ws = new WebSocket(`${websocketUrl}?conversation_id=${conversationId}`)
        
        ws.onopen = () => {
          if (!isMountedRef.current) {
            ws.close()
            return
          }
          reconnectAttemptRef.current = 0
          setState(prev => ({ ...prev, connectionStatus: "connected" }))
        }
        
        ws.onmessage = (event) => {
          if (!isMountedRef.current) return
          
          try {
            const message = JSON.parse(event.data)
            if (message.type === "ui_action") {
              handleUIAction(message.action as UIAction)
            }
          } catch (error) {
            console.error("[useUIActions] Error:", error)
          }
        }
        
        ws.onclose = () => {
          if (!isMountedRef.current) return
          
          setState(prev => ({ ...prev, connectionStatus: "disconnected" }))
          
          if (reconnectAttemptRef.current < MAX_RECONNECT_ATTEMPTS) {
            const delay = BASE_RECONNECT_DELAY * Math.pow(2, reconnectAttemptRef.current)
            reconnectAttemptRef.current += 1
            
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, delay)
          } else {
            setState(prev => ({ ...prev, connectionStatus: "error" }))
          }
        }
        
        ws.onerror = (error) => {
          setState(prev => ({ ...prev, connectionStatus: "error" }))
        }
        
        wsRef.current = ws
      } catch (error) {
        setState(prev => ({ ...prev, connectionStatus: "error" }))
      }
    }

    connectWebSocket()

    return () => {
      isMountedRef.current = false
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [websocketUrl, conversationId, handleUIAction, enableWebSocket])

  const sendPanelResponse = useCallback((panelType: SidePanelType, data: unknown) => {
    if (typeof window === 'undefined') return
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "panel_response",
        panel_type: panelType,
        data,
        conversation_id: conversationId
      }))
    }
  }, [conversationId])

  const reconnect = useCallback(() => {
    if (typeof window === 'undefined') return
    
    reconnectAttemptRef.current = 0
    if (wsRef.current) {
      wsRef.current.close()
    }
  }, [])

  return {
    activePanelType: state.activePanelType,
    activePanelData: state.activePanelData,
    activePanelTitle: state.activePanelTitle,
    isLoading: state.isLoading,
    pendingActions: state.pendingActions,
    isPanelOpen: state.activePanelType !== null,
    connectionStatus: state.connectionStatus,
    
    openPanel,
    closePanel,
    submitPanel,
    handleUIAction,
    handleChatCardAction,
    dismissAction,
    clearPendingActions,
    sendPanelResponse,
    reconnect
  }
}

export type UseUIActionsReturn = ReturnType<typeof useUIActions>
