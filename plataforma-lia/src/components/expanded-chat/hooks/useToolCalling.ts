'use client'

import { useState, useCallback, useRef } from 'react'
import { useAuthStore } from '@/stores/auth-store'

const BACKEND_URL = '/api/backend-proxy'

export interface ToolCall {
  tool_name: string
  parameters: Record<string, unknown>
  requires_confirmation: boolean
  confirmation_message?: string
}

export interface ToolExecutionResult {
  success: boolean
  message: string
  data?: unknown
  tool_name: string
  execution_time_ms: number
  error?: string
}

export interface UseToolCallingReturn {
  pendingToolCall: ToolCall | null
  executingTools: string[]
  completedTools: ToolExecutionResult[]
  toolError: string | null
  suggestToolCall: (toolCall: ToolCall) => void
  confirmToolCall: () => Promise<ToolExecutionResult>
  cancelToolCall: () => void
  executeToolDirectly: (toolName: string, params: Record<string, unknown>) => Promise<ToolExecutionResult>
  rollbackLastTool: () => Promise<ToolExecutionResult | null>
  hasPendingTool: boolean
  isExecuting: boolean
  clearError: () => void
  clearCompletedTools: () => void
}

export interface UseToolCallingOptions {
  maxCompletedTools?: number
  onToolExecuted?: (result: ToolExecutionResult) => void
  onToolError?: (error: string, toolName: string) => void
}

function getAuthHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
  }
}

function getUserId(): string {
  const user = useAuthStore.getState().user
  if (user?.id) return user.id
  return 'authenticated-user'
}

async function executeToolApi(
  toolName: string,
  parameters: Record<string, unknown>
): Promise<{ success: boolean; message: string; data?: unknown; error?: string }> {
  const userId = getUserId()
  const response = await fetch(`${BACKEND_URL}/orchestrator/execute-tool`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      tool_name: toolName,
      parameters,
      user_id: userId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    return {
      success: false,
      message: error.detail || 'Tool execution failed',
      error: error.detail || response.statusText,
    }
  }

  return response.json()
}

async function rollbackToolApi(
  toolName: string,
  executionData?: unknown
): Promise<{ success: boolean; message: string; error?: string }> {
  const userId = getUserId()
  const response = await fetch(`${BACKEND_URL}/orchestrator/rollback-tool`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      tool_name: toolName,
      execution_data: executionData,
      user_id: userId,
    }),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    return {
      success: false,
      message: error.detail || 'Rollback failed',
      error: error.detail || response.statusText,
    }
  }

  return response.json()
}

export function useToolCalling(options: UseToolCallingOptions = {}): UseToolCallingReturn {
  const { maxCompletedTools = 50, onToolExecuted, onToolError } = options

  const [pendingToolCall, setPendingToolCall] = useState<ToolCall | null>(null)
  const [executingTools, setExecutingTools] = useState<string[]>([])
  const [completedTools, setCompletedTools] = useState<ToolExecutionResult[]>([])
  const [toolError, setToolError] = useState<string | null>(null)

  const lastExecutedToolRef = useRef<ToolExecutionResult | null>(null)

  const clearError = useCallback(() => {
    setToolError(null)
  }, [])

  const clearCompletedTools = useCallback(() => {
    setCompletedTools([])
    lastExecutedToolRef.current = null
  }, [])

  const addCompletedTool = useCallback(
    (result: ToolExecutionResult) => {
      setCompletedTools((prev) => {
        const updated = [result, ...prev]
        if (updated.length > maxCompletedTools) {
          return updated.slice(0, maxCompletedTools)
        }
        return updated
      })
      lastExecutedToolRef.current = result
    },
    [maxCompletedTools]
  )

  const suggestToolCall = useCallback((toolCall: ToolCall) => {
    setPendingToolCall(toolCall)
    setToolError(null)
  }, [])

  const cancelToolCall = useCallback(() => {
    setPendingToolCall(null)
  }, [])

  const executeToolInternal = useCallback(
    async (toolName: string, params: Record<string, unknown>): Promise<ToolExecutionResult> => {
      const startTime = Date.now()
      setExecutingTools((prev) => [...prev, toolName])
      setToolError(null)

      try {
        const response = await executeToolApi(toolName, params)
        const executionTime = Date.now() - startTime

        const result: ToolExecutionResult = {
          success: response.success,
          message: response.message,
          data: response.data,
          tool_name: toolName,
          execution_time_ms: executionTime,
          error: response.error,
        }

        addCompletedTool(result)

        if (result.success) {
          onToolExecuted?.(result)
        } else {
          const errorMsg = result.error || result.message
          setToolError(errorMsg)
          onToolError?.(errorMsg, toolName)
        }

        return result
      } catch (err) {
        const executionTime = Date.now() - startTime
        const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'

        const result: ToolExecutionResult = {
          success: false,
          message: errorMessage,
          tool_name: toolName,
          execution_time_ms: executionTime,
          error: errorMessage,
        }

        addCompletedTool(result)
        setToolError(errorMessage)
        onToolError?.(errorMessage, toolName)

        return result
      } finally {
        setExecutingTools((prev) => prev.filter((t) => t !== toolName))
      }
    },
    [addCompletedTool, onToolExecuted, onToolError]
  )

  const confirmToolCall = useCallback(async (): Promise<ToolExecutionResult> => {
    if (!pendingToolCall) {
      const errorResult: ToolExecutionResult = {
        success: false,
        message: 'No pending tool call to confirm',
        tool_name: '',
        execution_time_ms: 0,
        error: 'No pending tool call',
      }
      setToolError(errorResult.error!)
      return errorResult
    }

    const { tool_name, parameters } = pendingToolCall
    setPendingToolCall(null)

    return executeToolInternal(tool_name, parameters)
  }, [pendingToolCall, executeToolInternal])

  const executeToolDirectly = useCallback(
    async (toolName: string, params: Record<string, unknown>): Promise<ToolExecutionResult> => {
      return executeToolInternal(toolName, params)
    },
    [executeToolInternal]
  )

  const rollbackLastTool = useCallback(async (): Promise<ToolExecutionResult | null> => {
    const lastTool = lastExecutedToolRef.current

    if (!lastTool || !lastTool.success) {
      setToolError('No successful tool execution to rollback')
      return null
    }

    const startTime = Date.now()
    const toolName = lastTool.tool_name

    setExecutingTools((prev) => [...prev, `rollback_${toolName}`])
    setToolError(null)

    try {
      const response = await rollbackToolApi(toolName, lastTool.data)
      const executionTime = Date.now() - startTime

      const result: ToolExecutionResult = {
        success: response.success,
        message: response.message,
        tool_name: `rollback_${toolName}`,
        execution_time_ms: executionTime,
        error: response.error,
      }

      if (result.success) {
        setCompletedTools((prev) => prev.filter((t) => t !== lastTool))
        lastExecutedToolRef.current = null
        onToolExecuted?.(result)
      } else {
        const errorMsg = result.error || result.message
        setToolError(errorMsg)
        onToolError?.(errorMsg, `rollback_${toolName}`)
      }

      return result
    } catch (err) {
      const executionTime = Date.now() - startTime
      const errorMessage = err instanceof Error ? err.message : 'Rollback failed'

      const result: ToolExecutionResult = {
        success: false,
        message: errorMessage,
        tool_name: `rollback_${toolName}`,
        execution_time_ms: executionTime,
        error: errorMessage,
      }

      setToolError(errorMessage)
      onToolError?.(errorMessage, `rollback_${toolName}`)

      return result
    } finally {
      setExecutingTools((prev) => prev.filter((t) => t !== `rollback_${toolName}`))
    }
  }, [onToolExecuted, onToolError])

  return {
    pendingToolCall,
    executingTools,
    completedTools,
    toolError,
    suggestToolCall,
    confirmToolCall,
    cancelToolCall,
    executeToolDirectly,
    rollbackLastTool,
    hasPendingTool: pendingToolCall !== null,
    isExecuting: executingTools.length > 0,
    clearError,
    clearCompletedTools,
  }
}
