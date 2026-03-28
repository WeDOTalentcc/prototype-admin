import { useState } from "react";
import {
  CheckCircle, AlertTriangle, XCircle, Target, Clock, Trophy,
  Mic2, BookOpen, Zap, AlertCircle, Info, Layers
} from "lucide-react";

const bigFive = [
  {
    trait: "Abertura a mudanças",
    hint: "Adapta-se a novidades, aprende rápido e lida bem com ambiguidade",
    vagaRelevancia: "critica",
    vagas: 70, candidato: 20, status: "gap",
    dreyfusEsperado: 4, dreyfusDemonstrado: 1,
  },
  {
    trait: "Organização e disciplina",
    hint: "Planejamento, atenção a prazos e execução sistemática",
    vagaRelevancia: "critica",
    vagas: 80, candidato: 50, status: "gap",
    dreyfusEsperado: 4, dreyfusDemonstrado: 2,
  },
  {
    trait: "Sociabilidade",
    hint: "Facilidade para interagir, comunicar e construir relacionamentos",
    vagaRelevancia: "moderada",
    vagas: 50, candidato: 40, status: "ok",
    dreyfusEsperado: 4, dreyfusDemonstrado: 3,
  },
  {
    trait: "Cooperação",
    hint: "Disposição para colaborar, ceder e trabalhar bem em equipe",
    vagaRelevancia: "critica",
    vagas: 75, candidato: 20, status: "gap",
    dreyfusEsperado: 4, dreyfusDemonstrado: 1,
  },
  {
    trait: "Estabilidade emocional",
    hint: "Mantém calma sob pressão e lida bem com críticas e frustrações",
    vagaRelevancia: "moderada",
    vagas: 60, candidato: 50, status: "ok",
    dreyfusEsperado: 4, dreyfusDemonstrado: 3,
  },
];

const gaps = [
  { texto: "Respostas predominantemente teóricas, sem aplicação prática comprovada", severidade: "alta" },
  { texto: "Nenhuma evidência de experiência com sistemas distribuídos", severidade: "alta" },
  { texto: "Raciocínio analítico demonstrado abaixo do nível mínimo esperado para a senioridade", severidade: "alta" },
  { texto: "Respostas sem estrutura Situação–Ação–Resultado nas perguntas comportamentais", severidade: "media" },
];

const alertas = [
  "Respostas muito curtas em 3 de 7 perguntas (menos de 30 palavras)",
  "Nível de abstração demonstrado abaixo do exigido para a senioridade da vaga",
];

const strengths = [
  "Entrega de resultados mensuráveis em projetos anteriores",
  "Proatividade relatada pelo próprio candidato",
];

const evidencias = [
  "Mencionou experiência com React e Node.js sem detalhar contexto",
  "Citou projeto sem métricas de resultado",
];

const perguntasEntrevista = [
  {
    pergunta: "Descreva uma situação específica em que você projetou uma solução de sistema distribuído. Qual era o problema, o que você fez e qual foi o resultado mensurado?",
    foco: "Sistemas distribuídos · Aplicação prática",
    severidade: "alta",
  },
  {
    pergunta: "Você pode detalhar um projeto onde demonstrou domínio técnico avançado? Precisamos entender o contexto, as alternativas consideradas e o impacto gerado.",
    foco: "Profundidade técnica · Estrutura de resposta",
    severidade: "alta",
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

export function Tab2Pendente() {
  const [hintOpen, setHintOpen] = useState<string | null>(null);
  const wsiScore = 2.7;
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
                <h1 className="text-base font-semibold text-gray-900">Detalhes da Triagem WSI — [DEMO] Thiago Pereira Nunes</h1>
                <p className="text-xs text-gray-500">Desenvolvedor Full Stack · São Paulo, SP</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <span className="bg-amber-100 text-amber-700 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> Revisão Necessária
              </span>
              <span className="text-[10px] font-medium text-amber-600 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                Revisão recomendada
              </span>
            </div>
          </div>
          <div className="flex items-center gap-6 text-sm flex-wrap">
            <div><p className="text-xs text-gray-400">Score WSI</p><p className={`font-bold ${classificacao.color}`}>{wsiScore}<span className="text-gray-400 font-normal">/5.0</span></p></div>
            <div><p className="text-xs text-gray-400">Ranking</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Trophy className="w-3.5 h-3.5 text-gray-400" />#9 de 12</p></div>
            <div><p className="text-xs text-gray-400">Classificação</p><p className={`font-semibold ${classificacao.color}`}>{classificacao.label}</p></div>
            <div><p className="text-xs text-gray-400">Duração</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Clock className="w-3.5 h-3.5" />18 min</p></div>
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
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Sumário Executivo</h2>
          <p className="text-sm text-gray-700 leading-relaxed">
            Candidato demonstrou conhecimento superficial das tecnologias requeridas, com respostas predominantemente teóricas e sem evidências práticas de aplicação. O nível de raciocínio demonstrado está abaixo do exigido para a senioridade da posição. Revisão humana recomendada antes de qualquer decisão.
          </p>
        </div>

        {/* Alertas (só aparece quando há flags) */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-4 h-4 text-amber-600" />
            <h2 className="text-sm font-semibold text-amber-700">Pontos de Atenção</h2>
            <span className="ml-auto text-[10px] bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full font-medium border border-amber-200">Revisão humana recomendada</span>
          </div>
          <ul className="space-y-1.5">
            {alertas.map((a, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-amber-800">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 shrink-0" /> {a}
              </li>
            ))}
          </ul>
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
            <p className="text-xs font-medium text-red-600 mb-2 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> Gaps Identificados</p>
            <ul className="space-y-2">
              {gaps.map((g, i) => {
                const sev = severidadeConfig[g.severidade as keyof typeof severidadeConfig];
                return (
                  <li key={i} className={`flex items-start gap-2.5 text-xs text-gray-700 rounded-lg border px-3 py-2.5 ${sev.bg} ${sev.border}`}>
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
                <p key={i} className="flex items-center gap-1.5 text-xs text-gray-500 italic">
                  <Zap className="w-3 h-3 text-gray-300 shrink-0" /> {e}
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
            <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-red-400 rounded-sm inline-block" /> Candidato</span>
            <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-200 rounded-sm inline-block border border-gray-300" /> Esperado pela vaga</span>
          </div>

          <div className="space-y-5">
            {bigFive.map((b) => {
              const isGap = b.status === "gap";
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
                    {isGap
                      ? <span className="text-[9px] font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-200">⚠️ Gap</span>
                      : <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200">✓ OK</span>}
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
                      className={`absolute inset-y-0 left-0 h-1.5 top-0.5 rounded-full ${isGap ? "bg-red-400" : "bg-gray-600"}`}
                      style={{ width: `${b.candidato}%` }}
                    />
                  </div>

                  {/* Values */}
                  <div className="flex items-center justify-between text-[10px] text-gray-400">
                    <span>Candidato: <span className={`font-semibold ${isGap ? "text-red-500" : "text-gray-600"}`}>{b.candidato}%</span></span>
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
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
            <p className="text-sm font-semibold text-amber-700 mb-1">Revisão Humana Recomendada</p>
            <p className="text-xs text-amber-800 leading-relaxed">O perfil técnico demonstrado está abaixo do esperado para a senioridade da vaga. Recomenda-se revisão manual antes de avançar ou rejeitar definitivamente.</p>
          </div>
        </div>

        {/* Próximos Passos */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Próximos Passos</h2>
          <ol className="space-y-2">
            {["Revisar manualmente as respostas completas da triagem", "Avaliar se o perfil serve para uma posição de senioridade menor", "Contato com candidato apenas se houver reposicionamento de vaga"].map((p, i) => (
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
          <p className="text-xs text-gray-400">Use estas perguntas caso decida avançar para uma entrevista de sondagem</p>
          {perguntasEntrevista.map((p, i) => {
            const sev = severidadeConfig[p.severidade as keyof typeof severidadeConfig];
            return (
              <div key={i} className={`border rounded-lg p-4 space-y-2 ${sev.bg} ${sev.border}`}>
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

        {/* Feedback ao Candidato */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-3">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-blue-500" /> Feedback para o Candidato
          </h2>
          <p className="text-xs text-gray-500 italic">Aguardando decisão do recrutador para liberar feedback ao candidato.</p>
          <div className="bg-gray-50 border border-gray-100 rounded-lg p-3">
            <p className="text-[10px] text-gray-400 font-medium mb-0.5">Prévia do feedback (rascunho)</p>
            <p className="text-xs text-gray-600">Agradecemos sua participação na triagem. Suas respostas foram analisadas e entraremos em contato em breve com o próximo passo do processo.</p>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex items-center justify-between shadow-sm">
          <span className="text-xs text-gray-500">Decisão do Recrutador</span>
          <div className="flex gap-2">
            <button className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium border border-red-200 text-red-600 rounded-lg hover:bg-red-50">
              <XCircle className="w-3.5 h-3.5" /> Reprovar
            </button>
            <button className="flex items-center gap-1.5 px-4 py-2 text-xs font-medium bg-amber-500 text-white rounded-lg">
              <AlertTriangle className="w-3.5 h-3.5" /> Solicitar Revisão
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
