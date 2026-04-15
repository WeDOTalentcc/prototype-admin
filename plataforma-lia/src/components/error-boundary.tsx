"use client"

import React from "react"

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

/**
 * Global error boundary that catches render errors anywhere in the tree.
 * Wraps the entire app in layout.tsx to prevent white screens.
 *
 * In production, errors are also captured by Sentry (sentry.client.config.ts).
 */
export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.error('[ErrorBoundary] Uncaught error:', error)
    console.error('[ErrorBoundary] Component stack:', info.componentStack)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return <ErrorFallbackScreen error={this.state.error} onReset={this.handleReset} />
    }
    return this.props.children
  }
}

interface ErrorFallbackProps {
  error?: Error
  onReset?: () => void
}

function ErrorFallbackScreen({ error, onReset }: ErrorFallbackProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-lia-bg-secondary">
      <div className="max-w-md w-full mx-auto p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-6 h-6 text-lia-text-secondary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.962-.833-2.732 0L3.072 16.5c-.77.833.192 2.5 1.732 2.5z"
            />
          </svg>
        </div>

        <h1 className="text-lg font-semibold text-lia-text-primary mb-2">
          Algo deu errado
        </h1>
        <p className="text-sm text-lia-text-tertiary mb-6">
          Ocorreu um erro inesperado. Nossa equipe foi notificada automaticamente.
        </p>

        {process.env.NODE_ENV === "development" && error && (
          <pre className="text-left text-xs bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl p-3 mb-4 overflow-auto max-h-32 text-status-error dark:text-status-error">
            {error.message}
          </pre>
        )}

        <div className="flex gap-3 justify-center">
          {onReset && (
            <button
              onClick={onReset}
              className="px-4 py-2 text-sm font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-xl hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
            >
              Tentar novamente
            </button>
          )}
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-sm font-medium border border-lia-border-default dark:border-lia-border-default text-lia-text-secondary rounded-xl hover:bg-lia-bg-secondary dark:hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none"
          >
            Recarregar página
          </button>
        </div>
      </div>
    </div>
  )
}
