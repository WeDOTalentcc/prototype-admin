import React from "react";
import { 
  Brain, Search, Paperclip, Mic, Send, 
  Cpu, Clock, Briefcase, Users, Calendar, 
  TrendingUp, BarChart3, Settings, Plus,
  FileCheck, Share2, SearchUser, FileSearch,
  UserPlus, CalendarClock, UserCheck
} from "lucide-react";

export function DashboardHub() {
  return (
    <div className="flex flex-col h-[100dvh] bg-slate-50 font-sans text-slate-900 overflow-hidden">
      {/* Top Banner / Header */}
      <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-slate-200 shrink-0">
        <div className="flex items-center gap-4">
          <div className="bg-cyan-500 p-2 rounded-xl text-white">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-slate-900">Oi, eu sou a LIA.</h1>
            <p className="text-sm text-slate-500">Sua assistente de recrutamento inteligente.</p>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="hidden lg:flex items-center gap-6 px-6 py-2 bg-slate-50 rounded-lg border border-slate-100">
          <div className="flex flex-col">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Vagas Abertas</span>
            <span className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Briefcase className="w-4 h-4 text-cyan-500" /> 3
            </span>
          </div>
          <div className="w-px h-8 bg-slate-200"></div>
          <div className="flex flex-col">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Candidatos Hoje</span>
            <span className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Users className="w-4 h-4 text-cyan-500" /> 12
            </span>
          </div>
          <div className="w-px h-8 bg-slate-200"></div>
          <div className="flex flex-col">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Entrevistas Pendentes</span>
            <span className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-500" /> 2
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
            <Settings className="w-4 h-4" />
            Centro de Controle
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
            <Search className="w-5 h-5" />
          </button>
          <div className="w-9 h-9 bg-cyan-600 text-white rounded-full flex items-center justify-center font-semibold shadow-sm border-2 border-white ring-2 ring-slate-100 cursor-pointer">
            N
          </div>
        </div>
      </header>

      {/* Main Content Area - 3 Columns */}
      <main className="flex-1 flex overflow-hidden">
        
        {/* Left Column: Recent Conversations (Sidebar) */}
        <aside className="w-72 bg-white border-r border-slate-200 flex flex-col overflow-y-auto shrink-0 hidden md:flex">
          <div className="px-5 py-4 border-b border-slate-100">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              Conversas Recentes
            </h2>
          </div>
          <div className="p-3 space-y-1">
            {[
              { title: "Triagem Vaga Desenvolvedor...", time: "há 2 horas", active: false },
              { title: "Agendamento entrevistas UX", time: "há 5 horas", active: false },
              { title: "Resumo candidatos Marketing", time: "ontem", active: false },
              { title: "Status vaga Analista de Dados", time: "há 2 dias", active: false },
              { title: "Feedback entrevista João", time: "há 3 dias", active: false },
            ].map((chat, i) => (
              <button 
                key={i}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors flex items-start gap-3 group ${
                  chat.active ? 'bg-cyan-50 text-cyan-900' : 'hover:bg-slate-50 text-slate-600'
                }`}
              >
                <Brain className={`w-4 h-4 mt-0.5 shrink-0 ${chat.active ? 'text-cyan-500' : 'text-slate-400 group-hover:text-cyan-400'}`} />
                <div className="flex-1 overflow-hidden">
                  <p className={`truncate font-medium ${chat.active ? 'text-cyan-900' : 'text-slate-700'}`}>
                    {chat.title}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">{chat.time}</p>
                </div>
              </button>
            ))}
          </div>
        </aside>

        {/* Center Column: Prompt Hero */}
        <section className="flex-1 flex flex-col bg-slate-50/50 relative overflow-y-auto">
          <div className="flex-1 flex flex-col items-center justify-center p-8 max-w-3xl mx-auto w-full">
            
            <div className="w-20 h-20 bg-white rounded-2xl shadow-sm border border-slate-100 flex items-center justify-center mb-8 relative">
              <Brain className="w-10 h-10 text-cyan-500" />
              <div className="absolute -right-1 -top-1 w-4 h-4 bg-green-500 border-2 border-white rounded-full"></div>
            </div>

            <h2 className="text-2xl font-semibold text-slate-800 mb-2 text-center">
              Como posso ajudar hoje?
            </h2>
            <p className="text-slate-500 mb-8 text-center max-w-md">
              Descreva o que você precisa ou escolha uma das ações rápidas ao lado.
            </p>

            {/* Prompt Input */}
            <div className="w-full bg-white rounded-2xl shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] border border-slate-200 overflow-hidden flex flex-col transition-shadow focus-within:shadow-[0_8px_30px_-4px_rgba(6,182,212,0.15)] focus-within:border-cyan-300">
              <textarea 
                placeholder="Peça a LIA... (ex: Mostre-me os melhores candidatos para a vaga de Design)"
                className="w-full p-4 min-h-[120px] resize-none outline-none text-slate-700 placeholder:text-slate-400 bg-transparent text-lg"
              ></textarea>
              
              <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-t border-slate-100">
                <div className="flex items-center gap-1">
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium">
                    <Search className="w-4 h-4" />
                    <span className="hidden sm:inline">Pesquisar</span>
                  </button>
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium">
                    <Paperclip className="w-4 h-4" />
                    <span className="hidden sm:inline">Anexar</span>
                  </button>
                </div>
                
                <div className="flex items-center gap-2">
                  <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-lg transition-colors">
                    <Mic className="w-5 h-5" />
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-lg font-medium transition-colors shadow-sm">
                    <Send className="w-4 h-4" />
                    Enviar
                  </button>
                </div>
              </div>
            </div>

          </div>

          {/* Bottom Left Floating Trigger (Required constraint) */}
          <div className="absolute bottom-6 left-6">
            <button className="w-12 h-12 bg-white rounded-full shadow-lg border border-slate-200 flex items-center justify-center text-cyan-500 hover:bg-slate-50 transition-transform hover:scale-105">
              <Brain className="w-6 h-6" />
            </button>
          </div>
        </section>

        {/* Right Column: Quick Actions (Rail) */}
        <aside className="w-80 bg-white border-l border-slate-200 flex flex-col overflow-y-auto shrink-0 hidden lg:flex">
          <div className="px-5 py-4 border-b border-slate-100 sticky top-0 bg-white/95 backdrop-blur z-10">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Cpu className="w-4 h-4 text-slate-400" />
              Ações Rápidas
            </h2>
          </div>
          
          <div className="p-4 flex flex-col gap-2">
            {[
              { icon: Plus, title: "Crie uma nova vaga" },
              { icon: FileCheck, title: "Solicite aprovação de nova vaga" },
              { icon: Share2, title: "Compartilhe candidatos com gestor" },
              { icon: SearchUser, title: "Buscar candidatos" },
              { icon: FileSearch, title: "Consulte sobre candidato" },
              { icon: UserPlus, title: "Adicione novo candidato" },
              { icon: CalendarClock, title: "Reagende uma entrevista" },
              { icon: UserCheck, title: "Atualize status do candidato" },
            ].map((action, i) => (
              <button 
                key={i}
                className="flex items-center gap-3 p-3 w-full text-left bg-white border border-slate-200 rounded-xl hover:border-cyan-300 hover:bg-cyan-50/30 transition-all group shadow-sm hover:shadow"
              >
                <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-500 group-hover:bg-cyan-100 group-hover:text-cyan-600 transition-colors">
                  <action.icon className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 leading-snug">
                  {action.title}
                </span>
              </button>
            ))}
          </div>
        </aside>

      </main>
    </div>
  );
}
