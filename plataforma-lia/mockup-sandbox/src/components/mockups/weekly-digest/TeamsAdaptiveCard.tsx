export default function TeamsAdaptiveCard() {
  return (
    <div className="min-h-screen bg-[#f5f5f5] flex items-center justify-center p-6 font-['Segoe_UI',sans-serif]">
      <div className="w-full max-w-[560px]">
        <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
          <div className="h-1 bg-[#6264A7]" />

          <div className="p-5">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-9 h-9 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-sm font-semibold">
                LIA
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">LIA — Assistente de Recrutamento</p>
                <p className="text-xs text-gray-500">Resumo Semanal · 31 Mar 2026, 08:00</p>
              </div>
            </div>

            <h2 className="text-base font-semibold text-gray-900 mb-1">
              Resumo Semanal — Suas Vagas
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Olá Ana, aqui está o panorama da sua semana de recrutamento.
            </p>

            <div className="border border-gray-200 rounded-lg mb-3 overflow-hidden">
              <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left">
                <div className="flex items-center gap-2">
                  <span className="text-[#6264A7] text-lg">📊</span>
                  <span className="text-sm font-medium text-gray-800">Saúde do Pipeline</span>
                </div>
                <svg className="w-4 h-4 text-gray-400 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className="p-3 border-t border-gray-200 bg-white">
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-[#6264A7]">12</p>
                    <p className="text-xs text-gray-500">vagas ativas</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-emerald-600">87</p>
                    <p className="text-xs text-gray-500">candidatos triados</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-amber-600">5</p>
                    <p className="text-xs text-gray-500">entrevistas agendadas</p>
                  </div>
                </div>
                <p className="text-sm text-gray-600">
                  Seu pipeline movimentou 34 candidatos esta semana. A taxa de conversão triagem→entrevista subiu de 18% para 23%.
                </p>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg mb-3 overflow-hidden">
              <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left">
                <div className="flex items-center gap-2">
                  <span className="text-lg">⚠️</span>
                  <span className="text-sm font-medium text-gray-800">Vagas em Risco</span>
                  <span className="bg-amber-100 text-amber-800 text-xs font-medium px-2 py-0.5 rounded-full">3</span>
                </div>
                <svg className="w-4 h-4 text-gray-400 rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <div className="p-3 border-t border-gray-200 bg-white space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Eng. Backend Sr — TechCorp</p>
                    <p className="text-xs text-gray-500">Time-to-fill: 52 dias (meta: 35)</p>
                  </div>
                  <span className="bg-red-100 text-red-700 text-xs font-medium px-2 py-0.5 rounded-full">crítico</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Product Designer — Acme</p>
                    <p className="text-xs text-gray-500">Time-to-fill: 41 dias (meta: 30)</p>
                  </div>
                  <span className="bg-amber-100 text-amber-700 text-xs font-medium px-2 py-0.5 rounded-full">atenção</span>
                </div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Data Analyst — LogiStar</p>
                    <p className="text-xs text-gray-500">Pipeline parado há 8 dias, 0 novos candidatos</p>
                  </div>
                  <span className="bg-amber-100 text-amber-700 text-xs font-medium px-2 py-0.5 rounded-full">atenção</span>
                </div>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg mb-3 overflow-hidden">
              <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🛡️</span>
                  <span className="text-sm font-medium text-gray-800">Compliance e Fairness</span>
                  <span className="bg-emerald-100 text-emerald-800 text-xs font-medium px-2 py-0.5 rounded-full">OK</span>
                </div>
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            <div className="border border-gray-200 rounded-lg mb-4 overflow-hidden">
              <button className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🔬</span>
                  <span className="text-sm font-medium text-gray-800">Otimização e Aprendizado</span>
                </div>
                <svg className="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            </div>

            <button className="w-full bg-[#6264A7] hover:bg-[#4f5190] text-white text-sm font-medium py-2.5 px-4 rounded transition-colors">
              Ver detalhes completos no Chat LIA →
            </button>
          </div>

          <div className="px-5 py-3 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-400 text-center">
              Enviado automaticamente pela LIA · Para desativar, acesse Configurações → Notificações
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-4">
          Mockup — Microsoft Teams Adaptive Card
        </p>
      </div>
    </div>
  );
}
