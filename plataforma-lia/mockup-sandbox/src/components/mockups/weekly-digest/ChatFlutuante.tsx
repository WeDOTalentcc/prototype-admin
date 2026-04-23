export default function ChatFlutuante() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-end justify-end p-6">
      <div className="w-full max-w-[420px]">
        <div className="bg-white rounded-xl shadow-2xl overflow-hidden border border-slate-200">
          <div className="bg-gradient-to-r from-cyan-600 to-cyan-700 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-full bg-white/20 flex items-center justify-center">
                <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <span className="text-white font-semibold text-sm">Chat LIA</span>
              <span className="bg-white/20 text-white text-[10px] px-1.5 py-0.5 rounded-full">online</span>
            </div>
            <div className="flex items-center gap-1.5">
              <button className="text-white/70 hover:text-white p-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <button className="text-white/70 hover:text-white p-1">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div className="h-[520px] overflow-y-auto p-4 space-y-4 bg-slate-50">
            <div className="flex items-start gap-2">
              <div className="w-6 h-6 rounded-full bg-cyan-600 flex items-center justify-center text-white text-[10px] font-bold shrink-0 mt-1">
                L
              </div>
              <div className="flex-1">
                <div className="bg-white rounded-xl rounded-tl-sm p-4 shadow-sm border border-slate-100 space-y-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="bg-cyan-50 text-cyan-700 text-[10px] font-semibold px-2 py-0.5 rounded-full border border-cyan-200">
                      RESUMO SEMANAL
                    </span>
                    <span className="text-[10px] text-slate-400">31 Mar 2026</span>
                  </div>

                  <p className="text-sm text-slate-700">
                    Bom dia, Ana. Preparei o resumo da sua semana de recrutamento.
                  </p>

                  <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                    <p className="text-xs font-semibold text-slate-600 mb-2 uppercase tracking-wide">Pipeline</p>
                    <div className="flex items-center gap-4">
                      <div className="text-center">
                        <p className="text-xl font-bold text-cyan-700">12</p>
                        <p className="text-[10px] text-slate-500">vagas</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xl font-bold text-emerald-600">87</p>
                        <p className="text-[10px] text-slate-500">triados</p>
                      </div>
                      <div className="text-center">
                        <p className="text-xl font-bold text-amber-600">5</p>
                        <p className="text-[10px] text-slate-500">entrevistas</p>
                      </div>
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      Conversão triagem→entrevista subiu de 18% para 23% esta semana.
                    </p>
                  </div>

                  <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
                    <p className="text-xs font-semibold text-amber-700 mb-1.5">3 vagas precisam de atenção</p>
                    <ul className="space-y-1.5">
                      <li className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                        <p className="text-xs text-slate-600">
                          <span className="font-medium">Eng. Backend Sr — TechCorp:</span> 52 dias abertos (meta: 35). Considere ampliar sourcing.
                        </p>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        <p className="text-xs text-slate-600">
                          <span className="font-medium">Product Designer — Acme:</span> 41 dias (meta: 30). 2 candidatos em pipeline, mas nenhuma entrevista marcada.
                        </p>
                      </li>
                      <li className="flex items-start gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        <p className="text-xs text-slate-600">
                          <span className="font-medium">Data Analyst — LogiStar:</span> sem novos candidatos há 8 dias. O perfil pode precisar de ajuste.
                        </p>
                      </li>
                    </ul>
                  </div>

                  <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
                    <p className="text-xs font-semibold text-emerald-700 mb-1">Compliance e Fairness</p>
                    <p className="text-xs text-slate-600">
                      FairnessGuard não bloqueou nenhuma triagem esta semana. Todas as avaliações dentro dos limites de equidade. Nenhum alerta de compliance ativo.
                    </p>
                  </div>

                  <div className="bg-violet-50 rounded-lg p-3 border border-violet-200">
                    <p className="text-xs font-semibold text-violet-700 mb-1">Padrões e Otimização</p>
                    <p className="text-xs text-slate-600">
                      Os templates de JD com mais de 6 competências tiveram 30% menos candidaturas qualificadas. Considere limitar a 5 competências-chave. O A/B test do formato de feedback está em andamento (72% do sample coletado).
                    </p>
                  </div>
                </div>

                <div className="flex gap-2 mt-2">
                  <button className="text-xs bg-cyan-50 text-cyan-700 px-3 py-1.5 rounded-lg border border-cyan-200 hover:bg-cyan-100 transition-colors">
                    Detalhar vagas em risco
                  </button>
                  <button className="text-xs bg-slate-50 text-slate-600 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                    Ver métricas completas
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 border-t border-slate-200 bg-white">
            <div className="flex items-center gap-2">
              <input
                type="text"
                placeholder="Pergunte sobre o resumo..."
                className="flex-1 text-sm border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
                readOnly
              />
              <button className="bg-cyan-600 text-white p-2 rounded-lg hover:bg-cyan-700 transition-colors">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-slate-500 mt-4">
          Mockup — Chat Flutuante LIA (Mensagem Proativa)
        </p>
      </div>
    </div>
  );
}
