// Loading boundary for the /projetos route.
//
// Without this file, the Next.js App Router keeps the PREVIOUS page visible
// during the server fetch/compile of the projetos segment, then swaps. Since
// recruiters typically arrive from "Funil de Talentos" (the sibling route
// under "Recrutar", whose idle state renders the "Quem você procura hoje?"
// greeting), that page lingered on screen — perceived as a flash of the Funil
// before Projetos appeared. This skeleton mirrors ProjetosSection so the
// transition shows a Projetos skeleton instead of the stale Funil.
//
// Keep this as a LEAF-level loading.tsx only — do NOT add nested loading.tsx
// in projetos/[id] or projetos/new, nor at the parent (dashboard) level, to
// avoid the Turbopack parent+child compile deadlock documented in replit.md.

function ProjetoCardSkeleton() {
  return (
    <div className="rounded-md border border-lia-border-subtle bg-lia-bg-paper p-4 space-y-3 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-md bg-lia-bg-tertiary shrink-0" />
        <div className="flex-1 space-y-1.5">
          <div className="h-3.5 bg-lia-bg-tertiary rounded w-3/4" />
          <div className="h-3 bg-lia-bg-tertiary rounded w-1/3" />
        </div>
      </div>
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-1 flex-1 rounded-full bg-lia-bg-tertiary" />
        ))}
      </div>
    </div>
  )
}

export default function ProjetosLoading() {
  return (
    <div className="p-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="h-6 w-56 rounded bg-lia-bg-tertiary animate-pulse" />
          <div className="h-9 w-32 rounded-md bg-lia-bg-tertiary animate-pulse" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <ProjetoCardSkeleton />
          <ProjetoCardSkeleton />
          <ProjetoCardSkeleton />
        </div>
      </div>
    </div>
  )
}
