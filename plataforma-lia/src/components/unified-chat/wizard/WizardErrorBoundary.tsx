"use client"

import React from "react"
import { AlertTriangle, RefreshCw } from "lucide-react"

interface Props {
  children: React.ReactNode
  fallbackMessage?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * WizardErrorBoundary — catches panel rendering errors.
 * Shows a friendly fallback instead of crashing the entire chat.
 */
export class WizardErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 text-center space-y-3">
          <div className="w-10 h-10 mx-auto rounded-full bg-status-warning/10 flex items-center justify-center">
            <AlertTriangle className="w-5 h-5 text-status-warning" />
          </div>
          <div>
            <p className="text-sm font-medium text-lia-text-primary font-['Open_Sans',sans-serif]">
              {this.props.fallbackMessage || "Erro ao carregar painel"}
            </p>
            <p className="text-xs text-lia-text-tertiary font-['Open_Sans',sans-serif] mt-1">
              {this.state.error?.message || "Erro desconhecido"}
            </p>
          </div>
          <button
            onClick={this.handleReset}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md border border-lia-border-subtle text-xs font-medium text-lia-text-secondary hover:bg-lia-interactive-hover transition-colors font-['Open_Sans',sans-serif]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Tentar novamente
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
