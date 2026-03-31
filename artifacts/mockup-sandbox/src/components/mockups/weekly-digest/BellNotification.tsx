export default function BellNotification() {
  return (
    <div className="min-h-screen bg-slate-100 flex items-start justify-end p-6 pt-16">
      <div className="w-full max-w-[400px]">
        <div className="flex items-center justify-end mb-2 gap-3 pr-2">
          <div className="relative">
            <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
              1
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-white text-xs font-semibold">
            AP
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-800">Notificações</h3>
            <button className="text-xs text-cyan-600 hover:text-cyan-700 font-medium">Marcar todas como lidas</button>
          </div>

          <div className="divide-y divide-slate-100">
            <div className="p-4 bg-cyan-50/50 hover:bg-cyan-50 transition-colors cursor-pointer border-l-[3px] border-cyan-500">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-sm font-semibold text-slate-800">Resumo Semanal Disponível</p>
                    <span className="text-[10px] text-slate-400 whitespace-nowrap ml-2">há 2 min</span>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-2">
                    Seu resumo semanal está pronto. 3 vagas precisam de atenção, pipeline com 87 triados, compliance OK.
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <button className="text-[10px] bg-cyan-600 text-white px-2.5 py-1 rounded-md hover:bg-cyan-700 transition-colors font-medium">
                      Ver no Chat
                    </button>
                    <button className="text-[10px] text-slate-500 px-2.5 py-1 rounded-md hover:bg-slate-100 transition-colors border border-slate-200">
                      Dispensar
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-4 hover:bg-slate-50 transition-colors cursor-pointer opacity-60">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-sm font-medium text-slate-500">Candidato avançou no pipeline</p>
                    <span className="text-[10px] text-slate-400 ml-2">ontem</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Eng. Backend Sr — TechCorp: 1 candidato avançou para entrevista.
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 hover:bg-slate-50 transition-colors cursor-pointer opacity-60">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-slate-300 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-sm font-medium text-slate-500">JD aprovada pela LIA</p>
                    <span className="text-[10px] text-slate-400 ml-2">2 dias atrás</span>
                  </div>
                  <p className="text-xs text-slate-400">
                    Data Analyst — LogiStar: Job Description pontuou 8.4/10, publicada automaticamente.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="px-4 py-2.5 border-t border-slate-100 bg-slate-50">
            <button className="w-full text-xs text-cyan-600 hover:text-cyan-700 font-medium text-center">
              Ver todas as notificações →
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-slate-400 mt-4">
          Mockup — Bell Notification (Dropdown do Sino)
        </p>
      </div>
    </div>
  );
}
