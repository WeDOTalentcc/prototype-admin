import React from "react"

// Manual mock de framer-motion para testes vitest.
// framer-motion não está instalado no ambiente de teste do projeto.
// Todos os componentes animados (motion.div, motion.span, etc.) são
// renderizados como seus equivalentes HTML simples — sem animação.

type AnyProps = Record<string, unknown> & { children?: React.ReactNode }

const motion = new Proxy({} as Record<string, React.ComponentType<AnyProps>>, {
  get(_target, tag: string) {
    const Component = ({ children, ...props }: AnyProps) =>
      React.createElement(tag, props as React.HTMLAttributes<HTMLElement>, children)
    Component.displayName = `motion.${tag}`
    return Component
  },
})

const AnimatePresence = ({ children }: { children?: React.ReactNode }) =>
  React.createElement(React.Fragment, null, children)
AnimatePresence.displayName = "AnimatePresence"

export { motion, AnimatePresence }
