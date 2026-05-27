import { type Metadata } from "next"

export const metadata: Metadata = {
  title: "WeDo Design System — WeDoTalent",
  description: "Referência visual dos tokens do WeDo Design System",
}

export default function DesignSystemPage() {
  return (
    <div className="p-8 max-w-4xl mx-auto space-y-12">
      <h1 className="text-3xl font-semibold text-lia-text-primary dark:text-lia-text-primary">
        WeDo Design System — WeDoTalent
      </h1>

      {/* Cores */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Cores</h2>
        <div className="flex gap-4 flex-wrap">
          <div className="w-20 h-20 bg-wedo-cyan rounded-xl flex items-end p-2">
            <span className="text-white text-xs font-medium">cyan</span>
          </div>
          <div className="w-20 h-20 bg-status-success rounded-xl flex items-end p-2">
            <span className="text-white text-xs font-medium">success</span>
          </div>
          <div className="w-20 h-20 bg-status-error rounded-xl flex items-end p-2">
            <span className="text-white text-xs font-medium">error</span>
          </div>
          <div className="w-20 h-20 bg-status-warning rounded-xl flex items-end p-2">
            <span className="text-white text-xs font-medium">warning</span>
          </div>
        </div>
      </section>

      {/* Tipografia */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Tipografia</h2>
        <div className="space-y-2 p-4 border border-lia-border-default rounded-xl">
          <p className="font-sans text-base text-lia-text-primary dark:text-lia-text-primary">Inter — body text padrão (font-sans)</p>
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Open Sans — headings (via next/font)</p>
          <p className="text-base italic text-lia-text-primary dark:text-lia-text-secondary">Crimson Text — editorial (via next/font)</p>
        </div>
      </section>

      {/* Border Radius */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Border Radius</h2>
        <div className="flex gap-4 items-center flex-wrap">
          <div className="w-24 h-20 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-xl flex items-center justify-center text-xs text-center text-lia-text-secondary dark:text-lia-text-secondary">
            rounded-xl<br/>cards/modais
          </div>
          <div className="w-24 h-20 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-lg flex items-center justify-center text-xs text-center text-lia-text-secondary dark:text-lia-text-secondary">
            rounded-lg<br/>inputs
          </div>
          <div className="w-20 h-20 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full flex items-center justify-center text-xs text-center text-lia-text-secondary dark:text-lia-text-secondary">
            rounded-full<br/>avatares
          </div>
        </div>
      </section>

      {/* Sombras */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Sombras</h2>
        <div className="flex gap-6 flex-wrap">
          <div className="w-32 h-20 bg-lia-bg-primary dark:bg-lia-bg-secondary shadow-lia-sm rounded-xl flex items-center justify-center text-xs text-lia-text-secondary dark:text-lia-text-secondary">
            lia-sm
          </div>
          <div className="w-32 h-20 bg-lia-bg-primary dark:bg-lia-bg-secondary shadow-lia-md rounded-xl flex items-center justify-center text-xs text-lia-text-secondary dark:text-lia-text-secondary">
            lia-md
          </div>
          <div className="w-32 h-20 bg-lia-bg-primary dark:bg-lia-bg-secondary shadow-lia-lg rounded-xl flex items-center justify-center text-xs text-lia-text-secondary dark:text-lia-text-secondary">
            lia-lg
          </div>
        </div>
      </section>

      {/* Z-Index */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Z-Index Semântico</h2>
        <div className="p-4 border border-lia-border-default rounded-xl">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left border-b border-lia-border-subtle">
                <th className="pb-2 text-lia-text-secondary dark:text-lia-text-tertiary">Token</th>
                <th className="pb-2 text-lia-text-secondary dark:text-lia-text-tertiary">Valor</th>
                <th className="pb-2 text-lia-text-secondary dark:text-lia-text-tertiary">Uso</th>
              </tr>
            </thead>
            <tbody className="space-y-1">
              <tr className="">
                <td className="py-1 font-mono text-xs">z-overlay</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">60</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">sub-modais</td>
              </tr>
              <tr className="">
                <td className="py-1 font-mono text-xs">z-modal</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">9999</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">Dialog principal</td>
              </tr>
              <tr>
                <td className="py-1 font-mono text-xs">z-max</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">10000</td>
                <td className="py-1 text-lia-text-secondary dark:text-lia-text-tertiary">Sempre acima de tudo</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Tokens de bordas */}
      <section className="space-y-4">
        <h2 className="text-xl font-medium text-lia-text-primary dark:text-lia-text-primary">Border Tokens</h2>
        <div className="flex gap-4 flex-wrap">
          <div className="p-4 border border-lia-border-subtle rounded-xl text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
            border-lia-border-subtle
          </div>
          <div className="p-4 border border-lia-border-default rounded-xl text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
            border-lia-border-default
          </div>
          <div className="p-4 border border-lia-border-medium rounded-xl text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
            border-lia-border-medium
          </div>
        </div>
      </section>
    </div>
  )
}
