"use client"

import React from "react"

interface ErrorBoundarySectionProps {
  fallback?: React.ReactNode
  children: React.ReactNode
  onError?: (error: Error) => void
}

interface ErrorBoundarySectionState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundarySection extends React.Component<ErrorBoundarySectionProps, ErrorBoundarySectionState> {
  constructor(props: ErrorBoundarySectionProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundarySectionState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    this.props.onError?.(error)
    if (process.env.NODE_ENV === "production") {
      const sentry = typeof window !== "undefined" && (window as { Sentry?: { captureException: (e: Error, ctx?: object) => void } }).Sentry
      if (sentry) {
        sentry.captureException(error, { extra: { componentStack: info.componentStack } })
      } else {
        console.error("[ErrorBoundary]", error.message, info.componentStack)
      }
    }
  }

  handleReset = () => {
    this.setState({ hasError: false, error: undefined })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }
      return (
        <div className="flex items-center justify-center py-12 px-4 bg-lia-bg-secondary rounded-lg">
          <div className="max-w-sm w-full text-center">
            <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center mx-auto mb-3">
              <svg
                className="w-5 h-5 text-lia-text-secondary"
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
            <h3 className="text-sm font-semibold text-lia-text-primary mb-1">
              Algo deu errado
            </h3>
            <p className="text-xs text-lia-text-tertiary mb-4">
              Ocorreu um erro ao carregar esta seção.
            </p>
            {process.env.NODE_ENV === "development" && this.state.error && (
              <pre className="text-left text-xs bg-lia-bg-tertiary rounded-xl p-2 mb-3 overflow-auto max-h-24 text-status-error">
                {this.state.error.message}
              </pre>
            )}
            <button
              onClick={this.handleReset}
              className="px-4 py-2 text-xs font-medium bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-xl hover:bg-lia-bg-inverse transition-colors motion-reduce:transition-none"
            >
              Tentar novamente
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
