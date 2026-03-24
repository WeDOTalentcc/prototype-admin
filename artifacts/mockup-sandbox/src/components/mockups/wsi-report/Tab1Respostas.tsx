import { useState } from "react";
import {
  ChevronDown, ChevronUp, CheckCircle, AlertTriangle, XCircle,
  Target, Mic, Clock, Trophy, BarChart3, Star
} from "lucide-react";

const competencias = [
  {
    nome: "Arquitetura de Software",
    framework: "Competency-Based",
    score: 4.8,
    pergunta: "Descreva um projeto onde você teve que tomar decisões arquiteturais importantes. Qual foi o contexto, quais alternativas você considerou e qual foi o resultado?",
    resposta: "Liderei a migração de monolito para microsserviços usando DDD e strangler fig pattern. Analisei 3 alternativas, implementei event sourcing. Resultado: deploy de 2h para 15min, uptime 99.2% para 99.95%.",
    autodeclaracao: 4.8,
    contexto: 4.9,
    bloomDemonstrado: 5,
    bloomEsperado: 5,
    dreyfusDemonstrado: 5,
    dreyfusEsperado: 5,
    gap: "ok",
    evidencias: [
      "Trade-off analysis entre 3 alternativas",
      "Metrics-driven decision (uptime, deploy time)",
      "DDD + Event Sourcing implementation",
    ],
    resumo: "Demonstra domínio completo de arquitetura com decisões fundamentadas em métricas e trade-offs claros.",
  },
  {
    nome: "Desenvolvimento Full Stack",
    framework: "Dreyfus Model",
    score: 4.8,
    pergunta: "Você precisa implementar um sistema de notificações em tempo real que suporte 100k usuários simultâneos. Como você abordaria frontend, backend e infraestrutura?",
    resposta: "WebSocket com fallback SSE no frontend, Redis Pub/Sub + RabbitMQ no backend, sticky sessions no LB. Sistema de priorização por canal. Já suportei 150k conexões.",
    autodeclaracao: 4.7,
    contexto: 4.8,
    bloomDemonstrado: 5,
    bloomEsperado: 4,
    dreyfusDemonstrado: 5,
    dreyfusEsperado: 4,
    gap: "acima",
    evidencias: [
      "Solução com WebSocket + SSE fallback",
      "Experiência comprovada com 150k conexões",
      "Estratégia de priorização por canal",
    ],
    resumo: "Acima do esperado — demonstra profundidade além do nível sênior exigido.",
  },
  {
    nome: "Liderança Técnica",
    framework: "Competency-Based",
    score: 3.9,
    pergunta: "Conte uma situação onde você precisou influenciar uma decisão técnica importante sem ter autoridade formal sobre a equipe.",
    resposta: "Convenci o time a adotar TypeScript através de um POC comparativo. Apresentei dados de redução de bugs em produção.",
    autodeclaracao: 4.0,
    contexto: 3.8,
    bloomDemonstrado: 3,
    bloomEsperado: 4,
    dreyfusDemonstrado: 3,
    dreyfusEsperado: 4,
    gap: "gap",
    evidencias: [
      "POC comparativo realizado",
      "Dados de impacto apresentados",
    ],
    resumo: "Abordagem válida, mas resposta carece de detalhes sobre a dinâmica de influência e resultado mensurável.",
  },
];

const gapConfig = {
  ok: { label: "Alinhado", icon: CheckCircle, color: "text-emerald-600", bg: "bg-emerald-50", border: "border-emerald-200" },
  acima: { label: "Acima do esperado", icon: Star, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" },
  gap: { label: "Gap identificado", icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" },
};

const dreyfusLabel = (n: number) => ["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"][n] ?? n;
const bloomLabel = (n: number) => ["", "Recordar", "Compreender", "Aplicar", "Analisar", "Avaliar"][n] ?? n;

export function Tab1Respostas() {
  const [expanded, setExpanded] = useState<number | null>(0);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <div className="max-w-[820px] mx-auto p-6 space-y-4">

        {/* Modal Header */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center">
                <Target className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h1 className="text-base font-semibold text-gray-900">Detalhes da Triagem WSI — [DEMO] Lucas Mendes Silva</h1>
                <p className="text-xs text-gray-500">Desenvolvedor Full Stack · São Paulo, SP</p>
              </div>
            </div>
            <span className="bg-emerald-100 text-emerald-700 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1">
              <CheckCircle className="w-3.5 h-3.5" /> Aprovado
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div>
              <p className="text-xs text-gray-400">Score WSI</p>
              <p className="font-bold text-gray-900">4.8<span className="text-gray-400 font-normal">/5.0</span></p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Ranking</p>
              <p className="font-semibold text-gray-900 flex items-center gap-1"><Trophy className="w-3.5 h-3.5 text-amber-500" />#1 de 12</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Classificação</p>
              <p className="font-semibold text-emerald-600">Excelente</p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Duração</p>
              <p className="font-semibold text-gray-900 flex items-center gap-1"><Clock className="w-3.5 h-3.5" />47 min</p>
            </div>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1">
          <button className="flex-1 py-2 text-xs font-medium rounded-md bg-gray-900 text-white">Respostas e Avaliação</button>
          <button className="flex-1 py-2 text-xs font-medium rounded-md text-gray-500 hover:bg-gray-50">Parecer e Feedback</button>
          <button className="flex-1 py-2 text-xs font-medium rounded-md text-gray-500 hover:bg-gray-50">Ranking e Comparativo</button>
        </div>

        {/* Scores por Dimensão */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2 mb-4">
            <BarChart3 className="w-4 h-4" /> Scores por Dimensão
          </h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: "Geral", value: 4.8, pct: 95 },
              { label: "Comp. Técnicas", value: 4.8, pct: 96 },
              { label: "Comp. Comportamentais", value: 4.7, pct: 93 },
            ].map((s) => (
              <div key={s.label} className="text-center">
                <p className="text-3xl font-bold text-gray-900">{s.value}</p>
                <p className="text-xs text-gray-400 mb-2">{s.label} ({s.pct}%)</p>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className="h-full bg-gray-900 rounded-full" style={{ width: `${s.pct}%` }} />
                </div>
              </div>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-4 pt-3 border-t border-gray-100">
            <span className="flex items-center gap-1 text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
              <Mic className="w-3 h-3" /> Triagem por Voz
            </span>
            <span className="text-xs text-gray-500">↗ Top 5%</span>
            <span className="text-xs text-gray-400">25/01/2026, 12:00</span>
          </div>
        </div>

        {/* Respostas por Competência */}
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
          <button
            className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition-colors"
            onClick={() => {}}
          >
            <h2 className="text-sm font-semibold text-gray-700">Respostas por Competência ({competencias.length})</h2>
            <ChevronUp className="w-4 h-4 text-gray-400" />
          </button>

          <div className="divide-y divide-gray-100">
            {competencias.map((c, i) => {
              const gap = gapConfig[c.gap as keyof typeof gapConfig];
              const GapIcon = gap.icon;
              const isOpen = expanded === i;
              return (
                <div key={i}>
                  <button
                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors text-left"
                    onClick={() => setExpanded(isOpen ? null : i)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-800">{c.nome}</span>
                      <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{c.framework}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`text-sm font-bold ${c.score >= 4.5 ? "text-emerald-600" : c.score >= 3.5 ? "text-amber-600" : "text-red-500"}`}>
                        {c.score}/5.0
                      </span>
                      {isOpen ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                    </div>
                  </button>

                  {isOpen && (
                    <div className="px-4 pb-4 space-y-4 bg-gray-50/50">
                      {/* Question & Answer */}
                      <div className="space-y-2">
                        <div className="bg-white border border-gray-100 rounded-lg p-3">
                          <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Pergunta</p>
                          <p className="text-xs text-gray-700 leading-relaxed">{c.pergunta}</p>
                        </div>
                        <div className="bg-white border border-gray-100 rounded-lg p-3">
                          <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-1">Resposta do Candidato</p>
                          <p className="text-xs text-gray-800 leading-relaxed">{c.resposta}</p>
                        </div>
                      </div>

                      {/* Scores grid */}
                      <div className="grid grid-cols-4 gap-2">
                        {[
                          { label: "Autodeclaração", value: c.autodeclaracao },
                          { label: "Contexto", value: c.contexto },
                          { label: "Bloom", value: bloomLabel(c.bloomDemonstrado), sub: `Nível ${c.bloomDemonstrado}` },
                          { label: "Dreyfus", value: dreyfusLabel(c.dreyfusDemonstrado), sub: `Nível ${c.dreyfusDemonstrado}` },
                        ].map((s) => (
                          <div key={s.label} className="bg-white border border-gray-100 rounded-lg p-2 text-center">
                            <p className="text-[9px] text-gray-400 mb-1">{s.label}</p>
                            <p className="text-sm font-bold text-gray-900">{s.value}</p>
                          </div>
                        ))}
                      </div>

                      {/* ✨ NOVO — Nível esperado vs. demonstrado */}
                      <div className={`flex items-center justify-between rounded-lg border px-3 py-2.5 ${gap.bg} ${gap.border}`}>
                        <div className="flex items-center gap-2">
                          <GapIcon className={`w-3.5 h-3.5 ${gap.color}`} />
                          <span className={`text-xs font-medium ${gap.color}`}>Esperado pela vaga</span>
                        </div>
                        <div className="flex items-center gap-4 text-xs">
                          <div className="text-right">
                            <p className="text-[9px] text-gray-400">Bloom</p>
                            <p className={`font-semibold ${gap.color}`}>{bloomLabel(c.bloomEsperado)}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-[9px] text-gray-400">Dreyfus</p>
                            <p className={`font-semibold ${gap.color}`}>{dreyfusLabel(c.dreyfusEsperado)}</p>
                          </div>
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${gap.bg} ${gap.color} border ${gap.border}`}>
                            {gap.label}
                          </span>
                        </div>
                      </div>

                      {/* Evidências */}
                      <div>
                        <p className="text-[10px] text-gray-400 uppercase tracking-wide mb-2">Evidências</p>
                        <div className="flex flex-wrap gap-2">
                          {c.evidencias.map((e, j) => (
                            <span key={j} className="flex items-center gap-1 text-[11px] bg-white border border-gray-100 text-gray-600 px-2 py-1 rounded-full">
                              <CheckCircle className="w-3 h-3 text-emerald-500" /> {e}
                            </span>
                          ))}
                        </div>
                        <p className="text-xs text-gray-500 italic mt-2">{c.resumo}</p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
          <span className="text-xs text-gray-500">Decisão do Recrutador</span>
          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium border border-red-200 text-red-600 rounded-lg hover:bg-red-50">
              <XCircle className="w-3.5 h-3.5" /> Reprovar
            </button>
            <button className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium bg-gray-900 text-white rounded-lg">
              <CheckCircle className="w-3.5 h-3.5" /> Aprovar para Entrevista
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
