import { useState } from "react";
import {
  CheckCircle, AlertTriangle, XCircle, Target, Clock, Trophy,
  ChevronDown, ChevronUp, Mic2, BookOpen, Zap, AlertCircle
} from "lucide-react";

const bigFive = [
  { trait: "Abertura a mudanças", vagas: 70, candidato: 20, status: "gap" },
  { trait: "Organização e disciplina", vagas: 80, candidato: 50, status: "gap" },
  { trait: "Sociabilidade", vagas: 50, candidato: 40, status: "ok" },
  { trait: "Cooperação", vagas: 75, candidato: 20, status: "gap" },
  { trait: "Estabilidade emocional", vagas: 60, candidato: 50, status: "ok" },
];

const gaps = [
  { texto: "Respostas predominantemente teóricas, sem aplicação prática comprovada", severidade: "alta" },
  { texto: "Nenhuma evidência de experiência com sistemas distribuídos", severidade: "alta" },
  { texto: "Bloom cognitivo demonstrado abaixo do nível mínimo esperado (Nível 2 vs. Nível 4)", severidade: "alta" },
  { texto: "CBI incompleto — ausência de estrutura Situação-Ação-Resultado nas respostas", severidade: "media" },
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

const comportamental = [
  { nome: "Inovação", score: 2.1, desc: "Sem exemplos concretos de iniciativas inovadoras" },
  { nome: "Colaboração", score: 1.8, desc: "Resposta genérica sobre trabalho em equipe" },
  { nome: "Organização", score: 2.3, desc: "Relata organização pessoal mas sem evidências profissionais" },
  { nome: "Resiliência", score: 2.0, desc: "Não demonstrou como lidou com situações de pressão" },
];

const perguntasEntrevista = [
  {
    pergunta: "Descreva uma situação específica em que você projetou uma solução de sistema distribuído. Qual era o problema, o que você fez e qual foi o resultado mensurado?",
    foco: "Sistemas distribuídos · Bloom aplicação",
    severidade: "alta",
  },
  {
    pergunta: "Você pode detalhar um projeto onde demonstrou domínio técnico avançado? Precisamos entender o contexto, as alternativas consideradas e o impacto gerado.",
    foco: "Profundidade técnica · CBI-STAR",
    severidade: "alta",
  },
];

const severidadeConfig = {
  alta: { label: "ALTA", color: "text-red-600", bg: "bg-red-50", border: "border-red-200", dot: "bg-red-500" },
  media: { label: "MÉDIA", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500" },
  baixa: { label: "BAIXA", color: "text-gray-500", bg: "bg-gray-50", border: "border-gray-200", dot: "bg-gray-400" },
};

export function Tab2Pendente() {
  const [bigFiveOpen, setBigFiveOpen] = useState(false);

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
            <span className="bg-amber-100 text-amber-700 text-xs font-medium px-3 py-1 rounded-full flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" /> Revisão Necessária
            </span>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <div><p className="text-xs text-gray-400">Score WSI</p><p className="font-bold text-amber-600">2.7<span className="text-gray-400 font-normal">/5.0</span></p></div>
            <div><p className="text-xs text-gray-400">Ranking</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Trophy className="w-3.5 h-3.5 text-gray-400" />#9 de 12</p></div>
            <div><p className="text-xs text-gray-400">Classificação</p><p className="font-semibold text-amber-600">Abaixo do esperado</p></div>
            <div><p className="text-xs text-gray-400">Duração</p><p className="font-semibold text-gray-900 flex items-center gap-1"><Clock className="w-3.5 h-3.5" />18 min</p></div>
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
            Candidato demonstrou conhecimento superficial das tecnologias requeridas, com respostas predominantemente teóricas e sem evidências práticas de aplicação. O nível cognitivo demonstrado está abaixo do exigido para a senioridade da posição. Revisão humana recomendada antes de qualquer decisão.
          </p>
        </div>

        {/* ✨ NOVO — Alertas (só aparece quando há flags) */}
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

        {/* Análise Comportamental */}
        <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-semibold text-gray-700">Análise Comportamental</h2>
          <div className="space-y-3">
            {comportamental.map((c) => (
              <div key={c.nome}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gray-700">{c.nome}</span>
                  <span className="text-xs font-bold text-red-500">{c.score}/5.0</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-1">
                  <div className="h-full bg-red-400 rounded-full" style={{ width: `${(c.score / 5) * 100}%` }} />
                </div>
                <p className="text-[11px] text-gray-500">{c.desc}</p>
              </div>
            ))}
          </div>

          {/* Big Five colapsável */}
          <div className="border border-gray-100 rounded-lg overflow-hidden">
            <button
              className="w-full flex items-center justify-between px-3 py-2.5 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
              onClick={() => setBigFiveOpen(!bigFiveOpen)}
            >
              <span className="text-xs font-medium text-gray-600">Ver perfil de personalidade (vaga × candidato)</span>
              {bigFiveOpen ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />}
            </button>
            {bigFiveOpen && (
              <div className="p-4 space-y-3 bg-white">
                <div className="flex items-center gap-4 text-[10px] text-gray-400 mb-1">
                  <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-red-400 rounded-sm inline-block" /> Candidato</span>
                  <span className="flex items-center gap-1"><span className="w-3 h-1.5 bg-gray-200 rounded-sm inline-block border border-gray-300" /> Esperado pela vaga</span>
                </div>
                {bigFive.map((b) => {
                  const isGap = b.status === "gap";
                  return (
                    <div key={b.trait}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[11px] text-gray-700">{b.trait}</span>
                        {isGap
                          ? <span className="text-[9px] font-bold text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-200">⚠️ Gap</span>
                          : <span className="text-[9px] font-bold text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-full border border-emerald-200">✓ OK</span>}
                      </div>
                      <div className="relative h-3">
                        <div className="absolute inset-y-0 left-0 h-1.5 top-0.75 rounded-full bg-gray-200 border border-gray-300" style={{ width: `${b.vagas}%` }} />
                        <div className={`absolute inset-y-0 left-0 h-1.5 top-0.75 rounded-full ${isGap ? "bg-red-400" : "bg-gray-600"}`} style={{ width: `${b.candidato}%` }} />
                      </div>
                    </div>
                  );
                })}
                <p className="text-[10px] text-gray-400 pt-1">Baseado na análise comportamental da triagem</p>
              </div>
            )}
          </div>
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

        {/* ✨ NOVO — Perguntas para entrevista */}
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
