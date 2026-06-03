import { cn } from "@/lib/utils"

/**
 * Indicador discreto de ambiente.
 *
 * Dirigido por variável de ambiente (`NEXT_PUBLIC_APP_ENV` com fallback para
 * `APP_ENV`). Renderiza um selo fixo e fino no topo da tela quando o ambiente
 * NÃO é produção, evitando que devs confundam o Repl de testes (develop) com o
 * de produção (main). Em produção — ou quando a variável não está definida —
 * nada é renderizado para não poluir o consumo diário.
 *
 * Ver guia operacional: docs/operations/dois-ambientes-develop-main.md
 */

type EnvDescriptor = {
  label: string
  className: string
}

function resolveEnvironment(): EnvDescriptor | null {
  const raw = (
    process.env.NEXT_PUBLIC_APP_ENV ||
    process.env.APP_ENV ||
    ""
  )
    .trim()
    .toLowerCase()

  // Produção (ou variável ausente) → sem indicador.
  if (raw === "" || raw === "production" || raw === "prod" || raw === "main") {
    return null
  }

  if (
    raw === "development" ||
    raw === "develop" ||
    raw === "dev" ||
    raw === "testes" ||
    raw === "teste" ||
    raw === "test" ||
    raw === "staging" ||
    raw === "homolog"
  ) {
    return {
      label: "TESTES",
      className: "bg-amber-500 text-amber-950",
    }
  }

  // Qualquer outro valor não-produção: mostra o valor cru em caixa-alta.
  return {
    label: raw.toUpperCase(),
    className: "bg-amber-500 text-amber-950",
  }
}

export function EnvironmentBadge() {
  const env = resolveEnvironment()

  if (!env) return null

  return (
    <div
      aria-hidden="true"
      className="pointer-events-none fixed inset-x-0 top-0 z-toast flex justify-center"
    >
      <span
        className={cn(
          "rounded-b-md px-3 py-0.5 text-[10px] font-bold uppercase tracking-widest shadow-sm",
          env.className
        )}
      >
        Ambiente: {env.label}
      </span>
    </div>
  )
}
