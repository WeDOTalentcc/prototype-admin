import { useState } from "react";
import {
  CheckCircle, AlertTriangle, XCircle, Target, Clock, Trophy,
  Mic2, BookOpen, Star, Zap, Info, Layers
} from "lucide-react";

const bigFive = [
  {
    trait: "Abertura a mudanças",
    hint: "Adapta-se a novidades, aprende rápido e lida bem com ambiguidade",
    vagaRelevancia: "critica",
    vagas: 80, candidato: 75, status: "ok",
    dreyfusEsperado: 4, dreyfusDemonstrado: 4,
  },
  {
    trait: "Organização e disciplina",
    hint: "Planejamento, atenção a prazos e execução sistemática",
    vagaRelevancia: "critica",
    vagas: 70, candidato: 95, status: "acima",
    dreyfusEsperado: 4, dreyfusDemonstrado: 5,
  },
  {
    trait: "Sociabilidade",
    hint: "Facilidade para interagir, comunicar e construir relacionamentos",
    vagaRelevancia: "moderada",
    vagas: 50, candidato: 40, status: "ok",
    dreyfusEsperado: 4, dreyfusDemonstrado: 4,
  },
  {
    trait: "Cooperação",
    hint: "Disposição para colaborar, ceder e trabalhar bem em equipe",
    vagaRelevancia: "critica",
    vagas: 75, candidato: 40, status: "gap",
    dreyfusEsperado: 4, dreyfusDemonstrado: 2,
  },
  {
    trait: "Estabilidade emocional",
    hint: "Mantém calma sob pressão e lida bem com críticas e frustrações",
    vagaRelevancia: "moderada",
    vagas: 65, candidato: 80, status: "acima",
    dreyfusEsperado: 4, dreyfusDemonstrado: 5,
  },
];

const gaps = [
  { texto: "Poderia explorar mais tecnologias de edge computing", severidade: "baixa" },
  { texto: "Aprofundar conhecimento em observabilidade e SRE practices", severidade: "baixa" },
];

const strengths = [
  "Domínio avançado de arquitetura de microsserviços com DDD e event sourcing",
  "Experiência comprovada com sistemas de alta escala (150k+ conexões)",
  "Proficiência em GraphQL Federation e APIs complexas",
  "Abordagem sistemática de debugging com prevenção via CI/CD",
];

const evidencias = [
  "Migração monolito→microsserviços com uptime 99.95%",
  "API GraphQL com 200+ types e federation de 8 serviços",
  "Resolução de memory leak com post-mortem documentado",
];

const proximosPassos = [
  "Agendar entrevista técnica aprofundada",
  "Apresentar ao gestor da área",
  "Preparar proposta competitiva",
];

const perguntasEntrevista = [
  {
    pergunta: "Você já implementou estratégias de observabilidade em sistemas distribuídos? Descreva como instrumentou traces, métricas e logs de ponta a ponta.",
    foco: "Observabilidade e SRE",
    severidade: "baixa",
  },
  {
    pergunta: "Em um projeto com edge computing, quais trade-offs você consideraria entre latência, consistência e custo operacional?",
    foco: "Edge computing",
    severidade: "baixa",
  },
];

const severidadeConfig = {
  alta: { label: "ALTA", color: "text-red-600", bg: "bg-red-50", border: "border-red-200", dot: "bg-red-500" },
  media: { label: "MÉDIA", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500" },
  baixa: { label: "BAIXA", color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200", dot: "bg-gray-400" },
};

const relevanciaConfig = {
  critica: { label: "Crítica para esta vaga", color: "text-purple-700", bg: "bg-purple-50", border: "border-purple-200" },
  moderada: { label: "Moderada", color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200" },
};

const dreyfusLabel = (n: number) => ["", "Iniciante", "Básico", "Intermediário", "Avançado", "Especialista"][n] ?? n;

// Tabela 9.5 — Classificação por WSI Final (escala /5.0 = /10 ÷ 2)
function getClassificacao(score: number): { label: string; color: string } {
  if (score >= 4.5) return { label: "Excepcional", color: "text-emerald-700" };
  if (score >= 4.0) return { label: "Excelente",   color: "text-emerald-600" };
  if (score >= 3.5) return { label: "Alto",         color: "text-blue-600"   };
  if (score >= 3.0) return { label: "Médio",        color: "text-amber-600"  };
  if (score >= 2.25) return { label: "Abaixo da média", color: "text-orange-600" };
  return               { label: "Regular / Baixo", color: "text-red-600"    };
}

function DreyfusRow({ dreyfusEsperado, dreyfusDemonstrado }: { dreyfusEsperado: number; dreyfusDemonstrado: number }) {
  const delta = dreyfusDemonstrado - dreyfusEsperado;
  const isCritical = delta <= -2;
  const isAtencao = delta === -1;
  const isAcima = delta > 0;

  const color = isCritical
    ? "text-red-600"
    : isAtencao
    ? "text-amber-600"
    : isAcima
    ? "text-blue-600"
    : "text-emerald-600";
  const bg = isCritical
    ? "bg-red-50 border-red-200"
    : isAtencao
    ? "bg-amber-50 border-amber-200"
    : isAcima
    ? "bg-blue-50 border-blue-200"
    : "bg-emerald-50 border-emerald-200";
  const label = isCritical ? "Gap crítico" : isAtencao ? "Atenção" : isAcima ? "Acima" : "Alinhado";

  return (
    <div className={`flex items-center justify-between text-[10px] rounded-md border px-2.5 py-1.5 mt-1 ${bg}`}>
      <span className="text-gray-500">Maturidade comportamental</span>
      <div className="flex items-center gap-2">
        <span className="text-gray-400">
          Esperada para Sênior: <span className="font-medium text-gray-600">{dreyfusLabel(dreyfusEsperado)}</span>
        </span>
        <span className="text-gray-300">·</span>
        <span className="text-gray-400">
          Demonstrada: <span className={`font-semibold ${color}`}>{dreyfusLabel(dreyfusDemonstrado)}</span>
        </span>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-full border ${bg} ${color}`}>{label}</span>
      </div>
    </div>
  );
}

export function Tab2Aprovado() {
  const [hintOpen, setHintOpen] = useState<string | null>(null);
  const wsiScore = 4.8;
  const classificacao = getClassificacao(wsiScore);

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
            <div className="flex items-center gap-2">
              <span className="bg-emerald-100 text-emerald-700 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5" /> Aprovado
              </span>
              <span className="text-[10px] font-medium text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                Alta confiança
              </span>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm flex-wrap">
            <div><p className="text-xs text-gray-400">Score WSI</p><p className="font-bold text-gray-900">{wsiScore}<span className="text-gray-400 font-normal">/5.0</span></p></div>
            <div><p className="text-xs text-gray-400">Ranking</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Trophy className="w-3.5 h-3.5 text-amber-500" />#1 de 12</p></div>
            <div><p className="text-xs text-gray-400">Classificação</p><p className={`font-semibold ${classificacao.color}`}>{classificacao.label}</p></div>
            <div><p className="text-xs text-gray-400">Duração</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Clock className="w-3.5 h-3.5" />47 min</p></div>
            <div>
              <p className="text-xs text-gray-400">Modo de triagem</p>
              <p className="font-semibold text-gray-700 flex items-center gap-1"><Layers className="w-3.5 h-3.5 text-gray-400" /> Compact · 7 perguntas</p>
            </div>
          </div>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 bg-white border border-gray-200 rounded-lg p-1">
          <button className="flex-1 py-2 text-xs font-medium rounded-md text-gray-500">Respostas e Avaliação</button>
          <button className="flex-1 py-2 text-xs font-medium rounded-md bg-gray-900 text-white">Parecer e Feedback</button>
          <button className="flex-1 py-2 text-xs font-medium rounded-md text-gray-500">Ranking e Comparativo</button>
        </div>

        {/* Sumário Executivo */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Star className="w-4 h-4 text-amber-500" /> Sumário Executivo
          </h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            Candidata excepcional com domínio completo de arquitetura, desenvolvimento full stack e liderança técnica. Demonstra capacidade de tomar decisões fundamentadas em métricas, resolver problemas complexos sistematicamente e liderar times com impacto mensurável. Altamente recomendada para posições de liderança técnica sênior.
          </p>
        </div>

        {/* Análise Técnica */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">Análise Técnica</h2>

          <div>
            <p className="text-xs font-medium text-emerald-700 mb-2 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> Pontos Fortes</p>
            <ul className="space-y-1.5">
              {strengths.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                  <CheckCircle className="w-3.5 h-3.5 text-emerald-500 mt-0.5 shrink-0" /> {s}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-600 mb-2 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Gaps Identificados</p>
            <ul className="space-y-2">
              {gaps.map((g, i) => {
                const sev = severidadeConfig[g.severidade as keyof typeof severidadeConfig];
                return (
                  <li key={i} className={`flex items-start gap-2.5 text-xs text-gray-700 rounded-lg border px-3 py-2 ${sev.bg} ${sev.border}`}>
                    <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${sev.dot}`} />
                    <span className="flex-1">{g.texto}</span>
                    <span className={`text-[9px] font-bold tracking-wider shrink-0 ${sev.color}`}>{sev.label}</span>
                  </li>
                );
              })}
            </ul>
          </div>

          <div>
            <p className="text-xs font-medium text-gray-500 mb-2">Evidências</p>
            <div className="space-y-1">
              {evidencias.map((e, i) => (
                <p key={i} className="flex items-center gap-1.5 text-xs text-gray-600">
                  <Zap className="w-3 h-3 text-gray-400 shrink-0" /> {e}
                </p>
              ))}
            </div>
          </div>
        </div>

        {/* Perfil de Personalidade — Big Five */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-gray-700">Perfil de Personalidade</h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Para esta vaga (Dev Full Stack Sênior), as dimensões <span className="text-purple-600 font-medium">Críticas</span> determinam o fit de performance e cultura.
            </p>
          </div>

          {/* Legend */}
          <div className="flex items-center gap-4 text-[10px] text-gray-400">
            <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-800 rounded-sm inline-block" /> Candidato</span>
            <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-200 rounded-sm inline-block border border-gray-300" /> Esperado pela vaga</span>
          </div>

          <div className="space-y-5">
            {bigFive.map((b) => {
              const isGap = b.status === "gap";
              const isAcima = b.status === "acima";
              const rel = relevanciaConfig[b.vagaRelevancia as keyof typeof relevanciaConfig];
              const showHint = hintOpen === b.trait;

              return (
                <div key={b.trait} className="space-y-1">
                  {/* Row: trait name + relevância + status + hint toggle */}
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-medium text-gray-800">{b.trait}</span>
                    <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded-full border ${rel.color} ${rel.bg} ${rel.border}`}>
                      {rel.label}
                    </span>
                    {isGap && <span className="text-[9px] font-bold text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-200">⚠️ Diferença</span>}
                    {isAcima && <span className="text-[9px] font-bold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-full border border-blue-200">↑ Acima</span>}
                    {!isGap && !isAcima && <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200">✓ Alinhado</span>}
                    <button
                      className="ml-auto"
                      onClick={() => setHintOpen(showHint ? null : b.trait)}
                      title="O que significa?"
                    >
                      <Info className="w-3 h-3 text-gray-300 hover:text-gray-500 transition-colors" />
                    </button>
                  </div>

                  {/* Hint tooltip */}
                  {showHint && (
                    <p className="text-[11px] text-gray-500 bg-gray-50 border border-gray-100 rounded-md px-2.5 py-1.5">
                      {b.hint}
                    </p>
                  )}

                  {/* Dual bar */}
                  <div className="relative h-3">
                    <div className="absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full bg-gray-200 border border-gray-300" style={{ width: `${b.vagas}%` }} />
                    <div
                      className={`absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full ${isGap ? "bg-amber-400" : isAcima ? "bg-blue-400" : "bg-gray-800"}`}
                      style={{ width: `${b.candidato}%` }}
                    />
                  </div>

                  {/* Values */}
                  <div className="flex items-center justify-between text-[10px] text-gray-400">
                    <span>Candidato: <span className="font-semibold text-gray-600">{b.candidato}%</span></span>
                    <span>Vaga espera: <span className="font-semibold text-gray-600">{b.vagas}%</span></span>
                  </div>

                  {/* Dreyfus comportamental */}
                  <DreyfusRow dreyfusEsperado={b.dreyfusEsperado} dreyfusDemonstrado={b.dreyfusDemonstrado} />
                </div>
              );
            })}
          </div>

          <p className="text-[10px] text-gray-400 pt-1 border-t border-gray-100">
            Clique em <Info className="w-2.5 h-2.5 inline" /> para entender o que cada dimensão mede. Baseado na análise comportamental da triagem WSI.
          </p>
        </div>

        {/* Recomendação */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Recomendação</h2>
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-emerald-700 mb-1">Fortemente Recomendado</p>
            <p className="text-xs text-emerald-800 leading-relaxed">Perfil excepcional que combina excelência técnica com habilidades de liderança. Candidata tem potencial para elevar a qualidade técnica de toda a equipe.</p>
          </div>
        </div>

        {/* Próximos Passos */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Próximos Passos</h2>
          <ol className="space-y-2">
            {proximosPassos.map((p, i) => (
              <li key={i} className="flex items-center gap-3 text-sm text-gray-700">
                <span className="w-6 h-6 rounded-full bg-gray-100 text-gray-600 text-xs font-bold flex items-center justify-center shrink-0">{i + 1}</span>
                {p}
              </li>
            ))}
          </ol>
        </div>

        {/* Perguntas sugeridas para a entrevista */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-3">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Mic2 className="w-4 h-4 text-gray-500" /> Perguntas sugeridas para a entrevista
          </h2>
          <p className="text-xs text-gray-400">Geradas com base nos gaps identificados — use na entrevista presencial</p>
          {perguntasEntrevista.map((p, i) => {
            const sev = severidadeConfig[p.severidade as keyof typeof severidadeConfig];
            return (
              <div key={i} className="border border-gray-100 rounded-lg p-4 space-y-2 bg-gray-50">
                <p className="text-xs text-gray-800 leading-relaxed">"{p.pergunta}"</p>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-400">Foco:</span>
                  <span className="text-[10px] text-gray-600 font-medium bg-white border border-gray-200 px-2 py-0.5 rounded-full">{p.foco}</span>
                  <span className={`text-[9px] font-bold ${sev.color}`}>Gap {sev.label}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Feedback para o Candidato */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-500" /> Feedback para o Candidato
          </h2>
          <p className="text-xs text-gray-600 leading-relaxed">
            Parabéns! Sua performance na triagem foi excelente e demonstrou alinhamento com as competências que buscamos para a posição de Desenvolvedor(a) Full Stack Sênior.
          </p>
          <div>
            <p className="text-xs font-medium text-gray-600 mb-1.5">Pontos Fortes Técnicos:</p>
            {["Forte domínio de arquitetura de software e padrões de design", "Experiência sólida com sistemas escaláveis e de alta disponibilidade"].map((s, i) => (
              <p key={i} className="flex items-center gap-1.5 text-xs text-gray-600 mb-1">
                <CheckCircle className="w-3 h-3 text-emerald-500 shrink-0" /> {s}
              </p>
            ))}
          </div>
          <div>
            <p className="text-xs font-medium text-gray-600 mb-1.5">Oportunidades de Desenvolvimento:</p>
            {["Explorar mais sobre edge computing e arquiteturas serverless", "Aprofundar conhecimento em observabilidade e SRE practices"].map((s, i) => (
              <p key={i} className="flex items-center gap-1.5 text-xs text-gray-600 mb-1">
                <BookOpen className="w-3 h-3 text-blue-400 shrink-0" /> {s}
              </p>
            ))}
          </div>
          <div className="bg-blue-50 border border-blue-100 rounded-lg p-3">
            <p className="text-[10px] text-blue-500 font-medium mb-0.5">Dica Personalizada</p>
            <p className="text-xs text-blue-700">Sua capacidade de fundamentar decisões com dados e métricas foi um destaque. Continue usando essa abordagem nas próximas etapas.</p>
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
