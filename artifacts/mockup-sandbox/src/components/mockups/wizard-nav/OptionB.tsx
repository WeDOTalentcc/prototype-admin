export function OptionB() {
  return (
    <div className="min-h-screen bg-slate-50 p-6 font-sans text-slate-900">
      <div className="mx-auto max-w-[1220px]">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight">
            Opção B — Kanban in-place (URL não muda)
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Manter o comportamento atual: forçar o modal a redirecionar para <code className="rounded bg-slate-200 px-1 text-xs">/pt-BR/vagas</code> antes
            de criar; o useEffect já existente troca a vista para o kanban da vaga recém-criada. Sem rota nova.
          </p>
        </header>

        <div className="grid grid-cols-2 gap-4">
          <Frame
            url="/pt-BR/vagas"
            label="ANTES — listagem"
          >
            <DashboardChrome>
              <ListingView highlightCreateButton />
            </DashboardChrome>
          </Frame>

          <Frame
            url="/pt-BR/vagas"
            label="DEPOIS — MESMA URL"
            tone="warning"
          >
            <DashboardChrome>
              <KanbanInPlace />
            </DashboardChrome>
          </Frame>
        </div>

        <ProsCons
          pros={[
            "Zero código novo de rota — usa o caminho que já funciona (useEffect em useJobsPageCore.ts:160)",
            "Implementação mais rápida: 1 linha no modal + redirect condicional",
            "Mantém o pós-mortem de 2026-04-29 (a rota /jobs/<id> foi removida por razão)",
            "Funciona bem para wizards curtos onde o usuário não precisa sair e voltar",
          ]}
          cons={[
            "URL não muda — recarregar a página perde o contexto e volta para a listagem",
            "Browser back/forward não funcionam como o usuário espera (back fecha o wizard inteiro)",
            "Impossível compartilhar link da vaga em criação (sem deep-link)",
            "Notificações, e-mails e tour 'continue de onde parou' precisam de mecanismo paralelo",
            "Se o usuário criar a vaga de OUTRO lugar (dashboard, chat), precisa redirect prévio — UX confusa (latência visível)",
          ]}
        />

        <div className="mt-4 rounded-xl bg-blue-50 p-4 ring-1 ring-blue-200">
          <div className="text-xs font-semibold text-blue-900">Como funciona hoje (estado atual quebrado)</div>
          <div className="mt-1 text-xs text-blue-900">
            O modal já tenta esse caminho, mas <code className="rounded bg-white px-1">navigateToJobDetail</code> é um no-op
            intencional e o fallback in-place SÓ dispara se o usuário já estiver em <code className="rounded bg-white px-1">/pt-BR/vagas</code>.
            Esta opção formaliza o caminho com redirect explícito.
          </div>
        </div>
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
  tone?: "neutral" | "warning";
  children: React.ReactNode;
}) {
  const badge =
    tone === "warning"
      ? "bg-amber-100 text-amber-900 ring-amber-200"
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

function KanbanInPlace() {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-3 py-2">
        <div className="flex items-center gap-2">
          <button className="text-[10px] text-slate-500 hover:text-slate-700">‹ Voltar para Vagas</button>
          <span className="text-[10px] text-slate-300">|</span>
          <span className="text-xs font-semibold text-slate-900">Engenheiro(a) de Plataforma</span>
        </div>
        <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[9px] text-amber-800">Rascunho</span>
      </div>
      <div className="grid flex-1 grid-cols-4 gap-1.5 overflow-hidden p-2">
        {["Triagem", "Entrevista", "Teste", "Oferta"].map((stage) => (
          <div key={stage} className="flex flex-col rounded-md bg-white p-2 ring-1 ring-slate-200">
            <div className="mb-1.5 flex items-center justify-between">
              <span className="text-[9px] font-semibold uppercase text-slate-600">{stage}</span>
              <span className="text-[8px] text-slate-400">0</span>
            </div>
            <div className="flex-1 rounded border border-dashed border-slate-200" />
          </div>
        ))}
      </div>
      <div className="border-t border-slate-200 bg-slate-100 px-3 py-1.5 text-[9px] text-slate-500">
        URL não mudou. F5 recarrega a listagem, não esta vista.
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
