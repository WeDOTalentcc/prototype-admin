import React from "react";
import {
  Brain,
  Search,
  Paperclip,
  Mic,
  Send,
  Cpu,
  Clock,
  Plus,
  FileText,
  Users,
  Calendar,
  UserPlus,
  ArrowRight,
  Settings,
  MessageSquare,
  CheckCircle,
} from "lucide-react";

export function BentoMosaic() {
  const recentChats = [
    { id: 1, title: "Triagem Vaga Desenvolvedor Front-end", time: "há 2 horas" },
    { id: 2, title: "Aprovação de vaga: Analista de Marketing", time: "há 5 horas" },
    { id: 3, title: "Busca de candidatos C-Level", time: "ontem" },
    { id: 4, title: "Reagendamento entrevista João Silva", time: "ontem" },
    { id: 5, title: "Feedback candidatos UX Design", time: "há 2 dias" },
  ];

  const suggestions = [
    {
      id: "create-job",
      title: "Crie uma nova vaga",
      description: "Descreva o perfil e eu gero a descrição completa, requisitos e defino a estratégia de atração.",
      icon: Plus,
      color: "bg-cyan-50 text-cyan-600",
      colSpan: "col-span-1 md:col-span-2",
      rowSpan: "row-span-1 md:row-span-2",
      featured: true,
    },
    {
      id: "search",
      title: "Buscar candidatos",
      description: "Encontre os melhores talentos em nossa base de dados com filtros avançados.",
      icon: Users,
      color: "bg-indigo-50 text-indigo-600",
      colSpan: "col-span-1 md:col-span-2",
      rowSpan: "row-span-1",
      featured: true,
    },
    {
      id: "approve",
      title: "Solicite aprovação de nova vaga",
      description: "Inicie o fluxo de aprovação com os gestores responsáveis.",
      icon: CheckCircle,
      color: "bg-emerald-50 text-emerald-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
    {
      id: "share",
      title: "Compartilhe candidatos com gestor",
      description: "Gere um relatório executivo para o hiring manager.",
      icon: ArrowRight,
      color: "bg-purple-50 text-purple-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
    {
      id: "consult",
      title: "Consulte sobre candidato",
      description: "Resumo rápido de perfil e histórico.",
      icon: Search,
      color: "bg-amber-50 text-amber-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
    {
      id: "add",
      title: "Adicione novo candidato",
      description: "Faça upload de currículos manualmente.",
      icon: UserPlus,
      color: "bg-blue-50 text-blue-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
    {
      id: "reschedule",
      title: "Reagende uma entrevista",
      description: "Sincronize agendas facilmente.",
      icon: Calendar,
      color: "bg-rose-50 text-rose-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
    {
      id: "update",
      title: "Atualize status do candidato",
      description: "Mova talentos pelo funil de contratação.",
      icon: FileText,
      color: "bg-slate-100 text-slate-600",
      colSpan: "col-span-1",
      rowSpan: "row-span-1",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col relative font-sans selection:bg-cyan-100">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="bg-cyan-500 text-white p-2 rounded-xl shadow-sm shadow-cyan-500/20">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-slate-800">LIA</h1>
            <p className="text-xs text-slate-500">Recrutamento Inteligente</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-full hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-sm">
            <Settings className="w-4 h-4" />
            Centro de Controle
          </button>
          <button className="text-slate-400 hover:text-slate-600 transition-colors">
            <Search className="w-5 h-5" />
          </button>
          <button className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-white font-medium text-sm shadow-sm ring-2 ring-white">
            N
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto pb-32">
        <div className="max-w-5xl mx-auto px-6 py-8">
          
          {/* Greeting & Horizontal Recents */}
          <div className="mb-10">
            <h2 className="text-2xl md:text-3xl font-bold text-slate-800 mb-2">
              Oi, eu sou a LIA.
            </h2>
            <p className="text-slate-600 mb-6 max-w-2xl">
              Sua assistente de recrutamento inteligente. O que vamos resolver hoje?
            </p>

            {/* Recents Strip */}
            <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide -mx-6 px-6 md:mx-0 md:px-0">
              {recentChats.map((chat) => (
                <button
                  key={chat.id}
                  className="flex-shrink-0 flex items-center gap-3 bg-white border border-slate-200 rounded-2xl px-4 py-3 hover:border-cyan-300 hover:shadow-md hover:shadow-cyan-500/5 transition-all group min-w-[240px] max-w-[280px]"
                >
                  <div className="bg-slate-50 p-2 rounded-lg group-hover:bg-cyan-50 transition-colors">
                    <MessageSquare className="w-4 h-4 text-slate-400 group-hover:text-cyan-600" />
                  </div>
                  <div className="text-left overflow-hidden">
                    <p className="text-sm font-medium text-slate-700 truncate">{chat.title}</p>
                    <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                      <Clock className="w-3 h-3" /> {chat.time}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Bento Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 auto-rows-[minmax(140px,auto)]">
            {suggestions.map((item) => (
              <button
                key={item.id}
                className={`group relative bg-white rounded-3xl border border-slate-200 p-6 text-left hover:border-cyan-300 hover:shadow-lg hover:shadow-cyan-500/10 transition-all duration-300 overflow-hidden flex flex-col justify-between ${item.colSpan} ${item.rowSpan}`}
              >
                {item.featured && (
                  <div className="absolute -right-8 -top-8 w-32 h-32 bg-gradient-to-br from-white/0 to-current opacity-[0.03] rounded-full blur-2xl group-hover:opacity-10 transition-opacity pointer-events-none" />
                )}

                <div>
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110 ${item.color}`}>
                    <item.icon className="w-6 h-6" />
                  </div>
                  <h3 className={`font-semibold text-slate-800 mb-2 ${item.featured ? 'text-lg md:text-xl' : 'text-base'}`}>
                    {item.title}
                  </h3>
                  <p className={`text-slate-500 ${item.featured ? 'text-sm' : 'text-sm line-clamp-2'}`}>
                    {item.description}
                  </p>
                </div>

                <div className="mt-4 flex items-center text-xs font-medium text-slate-400 group-hover:text-cyan-600 transition-colors opacity-0 translate-y-2 group-hover:opacity-100 group-hover:translate-y-0">
                  Executar agora <ArrowRight className="w-3 h-3 ml-1" />
                </div>
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Sticky Bottom Prompt */}
      <div className="fixed bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-slate-50 via-slate-50 to-transparent pointer-events-none">
        <div className="max-w-3xl mx-auto relative pointer-events-auto">
          {/* Floating Brain */}
          <div className="absolute -left-16 bottom-4 hidden lg:flex items-center justify-center w-12 h-12 bg-cyan-600 rounded-2xl shadow-lg shadow-cyan-600/30 text-white cursor-pointer hover:scale-105 transition-transform">
            <Brain className="w-6 h-6" />
          </div>

          <div className="bg-white rounded-3xl border border-slate-200 shadow-xl shadow-slate-200/50 overflow-hidden focus-within:border-cyan-400 focus-within:ring-4 focus-within:ring-cyan-500/10 transition-all">
            <textarea
              placeholder="Peça a LIA..."
              className="w-full bg-transparent border-0 resize-none p-4 pb-12 focus:ring-0 text-slate-700 placeholder:text-slate-400 text-base"
              rows={2}
            />
            <div className="absolute bottom-3 left-4 right-3 flex items-center justify-between">
              <div className="flex items-center gap-1">
                <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors">
                  <Paperclip className="w-5 h-5" />
                </button>
                <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors">
                  <Search className="w-5 h-5" />
                </button>
              </div>
              <div className="flex items-center gap-2">
                <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors">
                  <Mic className="w-5 h-5" />
                </button>
                <button className="p-2 bg-cyan-600 text-white hover:bg-cyan-700 rounded-xl shadow-md shadow-cyan-600/20 transition-colors">
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
