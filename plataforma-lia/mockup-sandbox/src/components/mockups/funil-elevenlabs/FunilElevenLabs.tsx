import { useState } from "react";

const tabs = [
  { id: "todos", label: "Todos", icon: "👥", count: 1247 },
  { id: "favoritos", label: "Favoritos", icon: null, count: null },
  { id: "listas", label: "Listas", icon: null, count: null },
  { id: "buscas", label: "Buscas Salvas", icon: null, count: null },
];

const statusFilters = ["Novo", "Em triagem", "Aprovado", "Reprovado"];
const seniorityFilters = ["Júnior", "Pleno", "Sênior", "Especialista"];

const mockCandidates = [
  { name: "Ana Carolina Silva", title: "Senior Frontend Developer", company: "Nubank", location: "São Paulo, SP", score: 92, status: "Aprovado", seniority: "Sênior" },
  { name: "Bruno Oliveira Santos", title: "Full Stack Engineer", company: "iFood", location: "Campinas, SP", score: 87, status: "Em triagem", seniority: "Pleno" },
  { name: "Carla Mendes", title: "Product Designer", company: "VTEX", location: "Rio de Janeiro, RJ", score: 84, status: "Novo", seniority: "Pleno" },
  { name: "Diego Fernandes", title: "Backend Engineer", company: "Mercado Livre", location: "São Paulo, SP", score: 91, status: "Aprovado", seniority: "Sênior" },
  { name: "Elena Rodrigues", title: "Data Scientist", company: "Stone", location: "Rio de Janeiro, RJ", score: 78, status: "Em triagem", seniority: "Pleno" },
  { name: "Felipe Costa", title: "DevOps Engineer", company: "PagSeguro", location: "São Paulo, SP", score: 85, status: "Novo", seniority: "Sênior" },
  { name: "Gabriela Martins", title: "UX Researcher", company: "Loft", location: "São Paulo, SP", score: 80, status: "Em triagem", seniority: "Júnior" },
  { name: "Hugo Almeida", title: "Mobile Developer", company: "99", location: "Belo Horizonte, MG", score: 88, status: "Aprovado", seniority: "Pleno" },
];

function getInitials(name: string) {
  return name.split(" ").slice(0, 2).map(n => n[0]).join("").toUpperCase();
}

function getStatusColor(status: string) {
  switch (status) {
    case "Aprovado": return { bg: "bg-emerald-50", text: "text-emerald-700", dot: "bg-emerald-500" };
    case "Em triagem": return { bg: "bg-amber-50", text: "text-amber-700", dot: "bg-amber-500" };
    case "Novo": return { bg: "bg-blue-50", text: "text-blue-700", dot: "bg-blue-500" };
    case "Reprovado": return { bg: "bg-red-50", text: "text-red-700", dot: "bg-red-500" };
    default: return { bg: "bg-gray-50", text: "text-gray-700", dot: "bg-gray-500" };
  }
}

function getScoreColor(score: number) {
  if (score >= 90) return "text-emerald-600";
  if (score >= 80) return "text-amber-600";
  return "text-gray-500";
}

export function FunilElevenLabs() {
  const [activeTab, setActiveTab] = useState("todos");
  const [activeStatus, setActiveStatus] = useState<string | null>(null);
  const [activeSeniority, setActiveSeniority] = useState<string | null>(null);

  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Open Sans', -apple-system, BlinkMacSystemFont, sans-serif" }}>
      <div className="max-w-[1400px] mx-auto px-6 py-6">

        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[15px] font-semibold text-gray-900 tracking-[-0.01em]">
              Funil de Talentos
            </h1>
            <p className="text-[11px] text-gray-500 mt-0.5">
              1.247 candidatos na base
            </p>
          </div>
          <button className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" /></svg>
            Compartilhar Busca
          </button>
        </div>

        {/* Tabs — Eleven Labs pill style */}
        <div className="flex items-center gap-1 mb-5">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded-lg transition-colors
                ${activeTab === tab.id
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }
              `}
            >
              {tab.icon && <span className="text-[12px]">{tab.icon}</span>}
              {tab.label}
              {tab.count && activeTab === tab.id && (
                <span className="ml-0.5 text-[10px] font-semibold text-gray-400">
                  {tab.count.toLocaleString("pt-BR")}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Search bar */}
        <div className="relative mb-4">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
          <input
            type="text"
            placeholder="Buscar por nome, cargo, empresa ou habilidade..."
            className="w-full pl-10 pr-4 py-2 text-[11px] text-gray-900 placeholder-gray-400 bg-white border border-gray-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-gray-300 focus:border-gray-300 transition-colors"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
            <button className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium text-gray-500 border border-gray-200 rounded-md hover:bg-gray-50">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" /></svg>
              Filtros
            </button>
          </div>
        </div>

        {/* Quick filter pills */}
        <div className="flex items-center gap-2 mb-5 flex-wrap">
          {statusFilters.map(s => (
            <button
              key={s}
              onClick={() => setActiveStatus(activeStatus === s ? null : s)}
              className={`
                px-2.5 py-1 text-[11px] font-medium rounded-full border transition-colors
                ${activeStatus === s
                  ? "bg-gray-900 text-white border-gray-900"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }
              `}
            >
              {s}
            </button>
          ))}
          <div className="w-px h-4 bg-gray-200 mx-1" />
          {seniorityFilters.map(s => (
            <button
              key={s}
              onClick={() => setActiveSeniority(activeSeniority === s ? null : s)}
              className={`
                px-2.5 py-1 text-[11px] font-medium rounded-full border transition-colors
                ${activeSeniority === s
                  ? "bg-gray-900 text-white border-gray-900"
                  : "bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                }
              `}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="w-10 px-4 py-2.5">
                  <input type="checkbox" className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-500" />
                </th>
                <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Candidato</th>
                <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Cargo Atual</th>
                <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Localização</th>
                <th className="text-center px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Score</th>
                <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="text-left px-4 py-2.5 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Nível</th>
              </tr>
            </thead>
            <tbody>
              {mockCandidates.map((c, i) => {
                const statusStyle = getStatusColor(c.status);
                return (
                  <tr
                    key={i}
                    className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors cursor-pointer"
                  >
                    <td className="px-4 py-2.5">
                      <input type="checkbox" className="w-3.5 h-3.5 rounded border-gray-300 text-gray-900 focus:ring-gray-500" />
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-[10px] font-semibold text-gray-500 flex-shrink-0">
                          {getInitials(c.name)}
                        </div>
                        <div>
                          <div className="text-[11px] font-medium text-gray-900">{c.name}</div>
                          <div className="text-[10px] text-gray-400">{c.company}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-2.5 text-[11px] text-gray-600">{c.title}</td>
                    <td className="px-4 py-2.5 text-[11px] text-gray-500">{c.location}</td>
                    <td className="px-4 py-2.5 text-center">
                      <span className={`text-[12px] font-semibold ${getScoreColor(c.score)}`}>{c.score}</span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium ${statusStyle.bg} ${statusStyle.text}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${statusStyle.dot}`} />
                        {c.status}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-[11px] text-gray-500">{c.seniority}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Pagination */}
          <div className="flex items-center justify-between px-4 py-2.5 border-t border-gray-100 bg-white">
            <span className="text-[10px] text-gray-500">
              Mostrando 1-8 de 1.247 candidatos
            </span>
            <div className="flex items-center gap-1">
              <button className="px-2 py-1 text-[10px] text-gray-400 hover:text-gray-600 rounded">
                ← Anterior
              </button>
              <button className="px-2 py-1 text-[10px] font-medium text-white bg-gray-900 rounded">1</button>
              <button className="px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-50 rounded">2</button>
              <button className="px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-50 rounded">3</button>
              <span className="px-1 text-[10px] text-gray-400">...</span>
              <button className="px-2 py-1 text-[10px] text-gray-500 hover:bg-gray-50 rounded">156</button>
              <button className="px-2 py-1 text-[10px] text-gray-500 hover:text-gray-600 rounded">
                Próximo →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
