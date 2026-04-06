import React from "react";
import {
  Brain,
  Search,
  Paperclip,
  Mic,
  Send,
  Clock,
  MessageCircle,
  Briefcase,
  CheckSquare,
  Share2,
  UserSearch,
  UserPlus,
  Calendar,
  RefreshCcw,
  Settings,
  Plus
} from "lucide-react";

export function ConversationalWelcome() {
  const recentChats = [
    { title: "Análise de currículos - Vaga Dev Senior", time: "há 2 horas" },
    { title: "Agendamento com Maria Silva", time: "há 5 horas" },
    { title: "Busca de candidatos DevOps", time: "ontem" },
    { title: "Aprovação de vaga de UX", time: "ontem" },
  ];

  const suggestions = [
    { text: "Crie uma nova vaga", icon: Briefcase },
    { text: "Solicite aprovação de nova vaga", icon: CheckSquare },
    { text: "Compartilhe candidatos com gestor", icon: Share2 },
    { text: "Buscar candidatos", icon: Search },
    { text: "Consulte sobre candidato", icon: UserSearch },
    { text: "Adicione novo candidato", icon: UserPlus },
    { text: "Reagende uma entrevista", icon: Calendar },
    { text: "Atualize status do candidato", icon: RefreshCcw },
  ];

  return (
    <div className="flex h-[100dvh] w-full bg-slate-50 text-slate-800 font-sans overflow-hidden">
      {/* Left Sidebar - Recent Conversations */}
      <aside className="w-72 bg-white border-r border-slate-200 flex flex-col hidden md:flex shadow-sm z-10">
        <div className="h-16 px-4 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2 text-cyan-600 font-semibold">
            <div className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center">
              <Brain className="w-5 h-5 text-cyan-600" />
            </div>
            <span className="text-lg">LIA</span>
          </div>
          <button className="w-8 h-8 flex items-center justify-center rounded-full text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 transition-colors">
            <Plus className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-3 px-1">Conversas Recentes</h3>
          <div className="space-y-1">
            {recentChats.map((chat, i) => (
              <button key={i} className="w-full text-left p-2.5 rounded-xl hover:bg-slate-50 transition-colors group flex items-start gap-3">
                <MessageCircle className="w-4 h-4 text-slate-400 group-hover:text-cyan-500 mt-0.5 shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-700 group-hover:text-cyan-900 truncate">{chat.title}</p>
                  <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1.5">
                    <Clock className="w-3 h-3" /> {chat.time}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative h-full bg-slate-50">
        {/* Header */}
        <header className="h-16 flex items-center justify-end px-6 absolute top-0 right-0 w-full pointer-events-none z-20">
          <div className="flex items-center gap-3 pointer-events-auto">
            <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-full hover:bg-slate-50 hover:text-cyan-700 transition-colors shadow-sm">
              <Settings className="w-4 h-4" />
              Centro de Controle
            </button>
            <button className="w-9 h-9 flex items-center justify-center text-slate-500 bg-white border border-slate-200 rounded-full hover:text-cyan-600 hover:bg-slate-50 transition-colors shadow-sm">
              <Search className="w-4 h-4" />
            </button>
            <button className="w-9 h-9 rounded-full bg-cyan-600 text-white flex items-center justify-center font-semibold text-sm border-2 border-white shadow-sm hover:bg-cyan-700 transition-colors">
              N
            </button>
          </div>
        </header>

        {/* Conversation Area */}
        <div className="flex-1 overflow-y-auto px-4 sm:px-8 pt-24 pb-40 flex justify-center">
          <div className="w-full max-w-3xl mt-auto lg:mt-12">
            
            {/* LIA Greeting Message (Chat Bubble) */}
            <div className="flex items-end gap-3 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shrink-0 shadow-md mb-2">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white border border-slate-100 rounded-2xl rounded-bl-sm px-6 py-5 shadow-sm max-w-[85%]">
                <h2 className="text-slate-800 text-lg font-semibold mb-2 flex items-center gap-2">
                  Oi, eu sou a LIA <span className="text-xl">👋</span>
                </h2>
                <p className="text-slate-600 text-[15px] leading-relaxed">
                  Sua assistente de recrutamento inteligente. Posso te ajudar a gerenciar vagas, buscar candidatos ou analisar currículos.
                </p>
                <p className="text-slate-500 text-sm mt-3 pt-3 border-t border-slate-100">
                  Qual das tarefas abaixo quer que eu execute para você?
                </p>
              </div>
            </div>

            {/* Quick Replies (Suggestions) */}
            <div className="pl-14 pr-4 animate-in fade-in slide-in-from-bottom-4 duration-500 delay-150 fill-mode-both">
              <div className="flex flex-wrap gap-2.5">
                {suggestions.map((s, i) => {
                  const Icon = s.icon;
                  return (
                    <button 
                      key={i}
                      className="flex items-center gap-2 px-3.5 py-2 bg-white border border-slate-200 rounded-full text-sm font-medium text-slate-600 hover:bg-cyan-50 hover:border-cyan-200 hover:text-cyan-700 transition-all shadow-sm group"
                    >
                      <Icon className="w-4 h-4 text-cyan-500 group-hover:text-cyan-600" />
                      {s.text}
                    </button>
                  );
                })}
              </div>
            </div>

          </div>
        </div>

        {/* Pinned Input Bar */}
        <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent pt-12 pb-6 px-4 sm:px-8 pointer-events-none z-20">
          <div className="max-w-3xl mx-auto w-full pointer-events-auto">
            <div className="bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50 focus-within:border-cyan-400 focus-within:ring-4 focus-within:ring-cyan-400/10 transition-all">
              <textarea 
                placeholder="Peça a LIA..."
                className="w-full max-h-32 min-h-[60px] p-4 text-slate-700 bg-transparent border-none resize-none focus:outline-none placeholder:text-slate-400 text-[15px]"
                rows={1}
              />
              <div className="flex items-center justify-between px-3 pb-3">
                <div className="flex items-center gap-1">
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-slate-50 rounded-xl transition-colors">
                    <Search className="w-5 h-5" />
                  </button>
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-slate-50 rounded-xl transition-colors">
                    <Paperclip className="w-5 h-5" />
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-slate-50 rounded-xl transition-colors">
                    <Mic className="w-5 h-5" />
                  </button>
                  <button className="px-4 py-2 bg-cyan-600 text-white font-medium rounded-xl hover:bg-cyan-700 transition-all shadow-sm shadow-cyan-600/20 flex items-center gap-2">
                    Enviar
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            <div className="text-center mt-3">
              <p className="text-[11px] text-slate-400">
                A LIA é uma IA e pode cometer erros. Considere verificar informações importantes.
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Brain Icon (Mobile only, hidden on desktop since sidebar has it) */}
      <button className="md:hidden absolute bottom-28 right-4 w-12 h-12 bg-cyan-600 rounded-full shadow-lg flex items-center justify-center text-white hover:bg-cyan-700 transition-colors z-30">
        <Brain className="w-6 h-6" />
      </button>
    </div>
  );
}
