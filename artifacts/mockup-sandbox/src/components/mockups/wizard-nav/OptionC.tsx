export function OptionC() {
  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans text-slate-900">
      <div className="mx-auto max-w-[1220px]">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            Opção C — Modal/Drawer sobreposto
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Wizard abre como overlay flutuante sobre a página atual (similar a "Editar Vaga" e ao chat lateral hoje). URL
            não muda. Listagem fica visível ao fundo.
          </p>
        </header>

        <div className="grid grid-cols-2 gap-4">
          <Frame url="/pt-BR/vagas" label="ANTES — listagem">
            <DashboardChrome>
              <ListingView highlightCreateButton />
            </DashboardChrome>
          </Frame>

          <Frame url="/pt-BR/vagas" label="DEPOIS — drawer sobreposto" tone="info">
            <DashboardChrome>
              <ListingWithDrawer />
            </DashboardChrome>
          </Frame>
        </div>

        <ProsCons
          pros={[
            "Sem nova rota — contorna a remoção de /jobs/<id> sem reabrir o pós-mortem",
            "Listagem permanece em contexto: usuário vê o que está fazendo no panorama maior",
            "Fechar é trivial: ESC, clique fora ou X — padrão UX universal",
            "Ideal para fluxos opcionais/interrompíveis (criação em segundo plano)",
            "Funciona igual a partir de qualquer rota (dashboard, chat, sidebar) — não precisa redirect prévio",
          ]}
          cons={[
            "Espaço vertical limitado — wizards de 8 painéis ficam apertados ou exigem scroll duplo",
            "Sem URL própria (mesmo problema da Opção B: F5 perde contexto, sem deep-link)",
            "Modais aninhados são problemáticos (ex.: upload de JD, calibração avançada)",
            "Forms longos em drawer geram a sensação de 'janelinha' — pode parecer task menor do que é",
          ]}
        />
      </div>
    </div>
  );
}

function Frame({
  url,
  label,
  tone = "neutral",
  children,
}: {
  url: string;
  label: string;
  tone?: "neutral" | "info";
  children: React.ReactNode;
}) {
  const badge =
    tone === "info"
      ? "bg-violet-100 text-violet-900 ring-violet-200"
      : "bg-slate-100 text-slate-700 ring-slate-200";
  return (
    <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-100 px-3 py-2">
        <div className="flex gap-1.5">
          <span className="size-2.5 rounded-full bg-red-400" />
          <span className="size-2.5 rounded-full bg-yellow-400" />
          <span className="size-2.5 rounded-full bg-green-400" />
        </div>
        <div className="flex-1 truncate rounded-md bg-white px-2.5 py-1 text-xs text-slate-600 ring-1 ring-slate-200">
          plataforma.lia<span className="text-slate-400">{url}</span>
        </div>
        <span className={`rounded-md px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ring-1 ${badge}`}>
          {label}
        </span>
      </div>
      <div className="h-[300px] bg-slate-50">{children}</div>
    </div>
  );
}

function DashboardChrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full">
      <aside className="flex w-12 flex-col items-center gap-2 border-r border-slate-200 bg-slate-900 py-3">
        <div className="size-7 rounded-md bg-violet-500" />
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="size-6 rounded-md bg-slate-700/70" />
        ))}
      </aside>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  );
}

function ListingView({ highlightCreateButton = false }: { highlightCreateButton?: boolean }) {
  return (
    <div className="p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-slate-900">Vagas</div>
          <div className="text-[10px] text-slate-500">1 ativa de 5 disponíveis</div>
        </div>
        <button
          className={`rounded-md px-2.5 py-1 text-[11px] font-medium text-white ${
            highlightCreateButton ? "bg-violet-600 ring-2 ring-violet-300 ring-offset-1" : "bg-violet-600"
          }`}
        >
          + Nova Vaga
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-md bg-white p-2 ring-1 ring-slate-200">
            <div className="mb-1 h-2 w-3/4 rounded bg-slate-300" />
            <div className="h-1.5 w-1/2 rounded bg-slate-200" />
            <div className="mt-2 flex justify-between">
              <span className="rounded bg-emerald-100 px-1.5 py-0.5 text-[8px] text-emerald-700">Ativa</span>
              <span className="text-[8px] text-slate-400">3 cands.</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ListingWithDrawer() {
  return (
    <div className="relative h-full overflow-hidden">
      <div className="opacity-50">
        <ListingView />
      </div>
      <div className="absolute inset-0 bg-slate-900/30" />
      <div className="absolute right-0 top-0 h-full w-[58%] border-l border-slate-200 bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
          <div className="flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-violet-500" />
            <span className="text-xs font-semibold text-slate-900">Nova vaga · Engenheiro(a) de Plataforma</span>
          </div>
          <button className="text-slate-400 hover:text-slate-600" aria-label="Fechar">
            ✕
          </button>
        </div>
        <div className="flex h-[calc(100%-32px)]">
          <nav className="w-24 shrink-0 border-r border-slate-200 bg-slate-50 p-1.5">
            {["Geral", "Descrição", "Skills", "Cultura", "Pipeline", "Calibrar", "Publicar"].map((s, i) => (
              <div
                key={s}
                className={`mb-0.5 rounded px-1 py-0.5 text-[9px] ${
                  i === 0 ? "bg-violet-100 font-medium text-violet-900" : "text-slate-600"
                }`}
              >
                {i === 0 ? "● " : "○ "}
                {s}
              </div>
            ))}
          </nav>
          <main className="flex-1 overflow-y-auto p-2.5">
            <div className="text-[11px] font-semibold text-slate-900">Informações Gerais</div>
            <div className="mt-1.5 space-y-1">
              {["Cargo", "Senioridade", "Cidade", "Idiomas"].map((f) => (
                <div key={f} className="rounded border border-slate-200 p-1">
                  <div className="text-[8px] uppercase text-slate-400">{f}</div>
                  <div className="text-[9px] text-slate-700">…</div>
                </div>
              ))}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

function ProsCons({ pros, cons }: { pros: string[]; cons: string[] }) {
  return (
    <div className="mt-6 grid grid-cols-2 gap-4">
      <div className="rounded-xl bg-emerald-50 p-4 ring-1 ring-emerald-200">
        <div className="mb-2 text-sm font-semibold text-emerald-900">Vantagens</div>
        <ul className="space-y-1.5 text-xs text-emerald-900">
          {pros.map((p, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-0.5 text-emerald-600">✓</span>
              <span>{p}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200">
        <div className="mb-2 text-sm font-semibold text-amber-900">Custos / Trade-offs</div>
        <ul className="space-y-1.5 text-xs text-amber-900">
          {cons.map((c, i) => (
            <li key={i} className="flex gap-2">
              <span className="mt-0.5 text-amber-600">!</span>
              <span>{c}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
