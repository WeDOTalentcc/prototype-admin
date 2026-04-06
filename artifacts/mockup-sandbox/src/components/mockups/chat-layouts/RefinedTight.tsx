import React from "react";
import { Brain, Search, Paperclip, Mic, Send, Cpu, Plus, FileText, UserCheck, Calendar, RefreshCcw, Clock } from "lucide-react";

export function RefinedTight() {
  return (
    <div className="min-h-screen bg-white flex flex-col relative font-sans text-slate-900">
      {/* Top Header */}
      <header className="absolute top-0 right-0 p-4 flex items-center gap-3 z-10">
        <button className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-600 bg-white hover:bg-slate-50 rounded-full transition-colors border border-slate-200 shadow-sm">
          <Cpu className="w-4 h-4" />
          Centro de Controle
        </button>
        <button className="p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors">
          <Search className="w-5 h-5" />
        </button>
        <button className="w-8 h-8 rounded-full bg-slate-800 text-white flex items-center justify-center text-sm font-medium">
          N
        </button>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-8 max-w-3xl mx-auto w-full gap-6">
        
        {/* Greeting Area */}
        <div className="flex flex-col items-center text-center gap-3 mt-8">
          <div className="w-14 h-14 bg-cyan-50 rounded-2xl flex items-center justify-center shadow-sm border border-cyan-100">
            <Brain className="w-7 h-7 text-cyan-500" />
          </div>
          <div>
            <h1 className="text-2xl text-slate-800 tracking-tight flex items-baseline justify-center gap-1.5">
              <span className="font-light text-slate-500">Oi, eu sou a</span>
              <span className="font-serif font-bold text-3xl text-slate-900 tracking-normal" style={{ fontFamily: "Source Serif 4, Georgia, serif" }}>LIA.</span>
            </h1>
            <p className="text-slate-500 mt-1 text-sm font-medium">Como posso ajudar você hoje?</p>
          </div>
        </div>

        {/* Suggestion Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl">
          {[
            { icon: Plus, text: "Crie uma nova vaga" },
            { icon: FileText, text: "Solicite aprovacao de nova vaga" },
            { icon: UserCheck, text: "Compartilhe candidatos com gestor" },
            { icon: Search, text: "Buscar candidatos" },
            { icon: Search, text: "Consulte sobre candidato" },
            { icon: UserCheck, text: "Adicione novo candidato" },
            { icon: Calendar, text: "Reagende uma entrevista" },
            { icon: RefreshCcw, text: "Atualize status do candidato" }
          ].map((item, i) => (
            <button 
              key={i} 
              className="flex items-center gap-3 p-3 text-left border border-slate-200 rounded-xl bg-white transition-all duration-200 hover:scale-[1.02] hover:border-cyan-200 hover:shadow-sm group"
            >
              <div className="bg-cyan-50 text-cyan-600 rounded-lg p-1.5 transition-colors group-hover:bg-cyan-100">
                <item.icon className="w-4 h-4" />
              </div>
              <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900">{item.text}</span>
            </button>
          ))}
        </div>

        {/* Prompt Input */}
        <div className="w-full max-w-2xl relative group">
          <div className="absolute -inset-0.5 bg-cyan-100 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500"></div>
          <div className="relative bg-white border border-slate-200 rounded-2xl shadow-sm transition-all duration-200 focus-within:border-cyan-300 focus-within:ring-2 focus-within:ring-cyan-100 focus-within:shadow-md flex flex-col">
            <textarea 
              placeholder="Peca a LIA..." 
              className="w-full bg-transparent resize-none p-4 pb-12 outline-none text-slate-700 placeholder-slate-400 min-h-[100px] text-base rounded-2xl"
              spellCheck="false"
            />
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between">
              <div className="flex items-center gap-1">
                <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                  <Search className="w-4 h-4" />
                </button>
                <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                  <Paperclip className="w-4 h-4" />
                </button>
              </div>
              <div className="flex items-center gap-1">
                <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-lg transition-colors">
                  <Mic className="w-4 h-4" />
                </button>
                <button className="p-2 bg-slate-900 text-white hover:bg-slate-800 rounded-lg transition-colors shadow-sm">
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations */}
        <div className="w-full max-w-2xl mt-2 flex flex-col gap-2 pb-8">
          <div className="flex items-center justify-between px-2 mb-1">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Recentes</h2>
            <button className="text-xs text-slate-400 hover:text-slate-600 transition-colors font-medium">Limpar recentes</button>
          </div>
          <div className="flex flex-col gap-1.5">
            {[
              { title: "Análise de perfil - Desenvolvedor Senior", time: "Há 2 horas" },
              { title: "Rascunho de vaga: Gerente de Produto", time: "Ontem" },
              { title: "Triagem de candidatos para Design", time: "Há 2 dias" }
            ].map((item, i) => (
              <button key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 transition-all border-l-[3px] border-transparent hover:border-cyan-400 hover:shadow-sm bg-white text-left group">
                <Brain className="w-4 h-4 text-slate-300 group-hover:text-cyan-500 transition-colors flex-shrink-0" />
                <span className="text-sm font-medium text-slate-600 group-hover:text-slate-900 truncate flex-1 transition-colors">{item.title}</span>
                <span className="text-xs text-slate-400 whitespace-nowrap flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  {item.time}
                </span>
              </button>
            ))}
          </div>
        </div>

      </main>

      {/* Floating Bottom Left Icon */}
      <div className="absolute bottom-6 left-6 z-10">
        <button className="p-3 bg-white border border-slate-200 shadow-md hover:shadow-lg rounded-2xl text-cyan-500 hover:scale-105 transition-all">
          <Brain className="w-6 h-6" />
        </button>
      </div>

    </div>
  );
}

export default RefinedTight;
