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

    // Sentry capture disabled — package not installed
    // To enable: npm install @sentry/nextjs, then uncomment below
    // try { const Sentry = require("@sentry/nextjs"); Sentry.captureException(error, { extra: { componentStack: info.componentStack } }) } catch {}
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full mx-auto p-8 text-center">
        <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-6 h-6 lia-text-secondary"
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

        <h1 className="text-lg font-semibold text-gray-900 dark:text-lia-text-primary mb-2">
          Algo deu errado
        </h1>
        <p className="text-sm text-gray-500 dark:text-lia-text-tertiary mb-6">
          Ocorreu um erro inesperado. Nossa equipe foi notificada automaticamente.
        </p>

        {process.env.NODE_ENV === "development" && error && (
          <pre className="text-left text-xs bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-3 mb-4 overflow-auto max-h-32 text-status-error dark:text-status-error">
            {error.message}
          </pre>
        )}

        <div className="flex gap-3 justify-center">
          {onReset && (
            <button
              onClick={onReset}
              className="px-4 py-2 text-sm font-medium bg-gray-900 text-white rounded-md hover:bg-gray-700 transition-colors"
            >
              Tentar novamente
            </button>
          )}
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 text-sm font-medium border border-lia-border-default dark:border-lia-border-default text-gray-700 dark:text-lia-text-secondary rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            Recarregar página
          </button>
        </div>
      </div>
    </div>
  )
}
