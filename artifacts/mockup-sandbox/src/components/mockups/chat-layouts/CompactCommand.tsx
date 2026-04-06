import React from "react";
import {
  Brain,
  Search,
  Paperclip,
  Mic,
  Send,
  Clock,
  Settings,
  User,
  Plus,
  MessageSquare,
  Sparkles,
  Command
} from "lucide-react";

const SUGGESTIONS = [
  "Crie uma nova vaga",
  "Solicite aprovação",
  "Compartilhe candidatos",
  "Buscar candidatos",
  "Consulte sobre candidato",
  "Adicione novo candidato",
  "Reagende uma entrevista",
  "Atualize status do candidato",
];

const RECENT_CHATS = [
  { id: 1, title: "Triagem para Desenvolvedor Senior", time: "Há 2 horas" },
  { id: 2, title: "Aprovação de vaga: Gerente de Marketing", time: "Ontem, 14:30" },
  { id: 3, title: "Busca de candidatos DevOps", time: "Segunda, 09:15" },
  { id: 4, title: "Feedback da entrevista da Ana Silva", time: "12 de Out, 16:45" },
];

export function CompactCommand() {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col relative font-sans selection:bg-cyan-100 selection:text-cyan-900 overflow-hidden">
      {/* Top Navigation / Header (Minimal) */}
      <header className="absolute top-0 left-0 w-full p-4 md:p-6 flex justify-between items-center z-10">
        <div className="flex items-center gap-2 text-slate-800 font-semibold text-lg tracking-tight">
          <div className="w-8 h-8 rounded-lg bg-cyan-500 flex items-center justify-center text-white shadow-sm">
            <Brain className="w-5 h-5" />
          </div>
          LIA
        </div>
        <div className="flex items-center gap-3">
          <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-full transition-colors">
            <Search className="w-5 h-5" />
          </button>
          <button className="hidden md:flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-600 bg-white border border-slate-200 rounded-full hover:bg-slate-50 hover:text-slate-900 transition-all shadow-sm">
            <Settings className="w-4 h-4" />
            Centro de Controle
          </button>
          <button className="w-9 h-9 rounded-full bg-slate-200 border-2 border-white shadow-sm flex items-center justify-center text-sm font-bold text-slate-600 hover:ring-2 hover:ring-cyan-500 hover:ring-offset-2 transition-all">
            P
          </button>
        </div>
      </header>

      {/* Main Command Center */}
      <main className="flex-1 flex flex-col items-center justify-center w-full max-w-4xl mx-auto px-4 sm:px-6 z-0 mt-12 md:mt-0">
        
        {/* Helper Greeting */}
        <div className="flex flex-col items-center text-center mb-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
            Oi, eu sou a LIA.
            <Sparkles className="w-6 h-6 text-cyan-500" />
          </h1>
          <p className="text-slate-500 mt-2 text-lg">O que vamos realizar hoje?</p>
        </div>

        {/* Suggestion Pills (Horizontal Scroll) */}
        <div className="w-full max-w-3xl mb-4 relative animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
          {/* Fading edges for scroll area */}
          <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-slate-50 to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-slate-50 to-transparent z-10 pointer-events-none" />
          
          <div className="flex overflow-x-auto gap-2 pb-2 -mx-4 px-4 sm:mx-0 sm:px-0 no-scrollbar snap-x">
            {SUGGESTIONS.map((suggestion, i) => (
              <button
                key={i}
                className="snap-start shrink-0 px-4 py-2 rounded-full bg-white border border-slate-200 text-sm font-medium text-slate-600 hover:text-cyan-700 hover:border-cyan-200 hover:bg-cyan-50 transition-all shadow-sm flex items-center gap-2 group"
              >
                <Command className="w-3.5 h-3.5 text-slate-400 group-hover:text-cyan-500" />
                {suggestion}
              </button>
            ))}
          </div>
        </div>

        {/* The Command Input (Dominant Element) */}
        <div className="w-full max-w-3xl relative animate-in fade-in zoom-in-95 duration-500 delay-200">
          <div className="absolute -inset-1 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-3xl blur opacity-20 transition duration-1000 group-hover:opacity-30"></div>
          <div className="relative bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/60 overflow-hidden focus-within:ring-4 focus-within:ring-cyan-500/20 focus-within:border-cyan-500 transition-all duration-300 flex flex-col">
            <textarea
              placeholder="Digite um comando, pesquise por candidatos, ou faça uma pergunta..."
              className="w-full h-32 md:h-40 resize-none bg-transparent p-5 md:p-6 text-lg md:text-xl text-slate-800 placeholder:text-slate-400 focus:outline-none"
              autoFocus
            />
            
            {/* Input Action Bar */}
            <div className="flex items-center justify-between p-3 bg-slate-50/80 border-t border-slate-100 backdrop-blur-sm">
              <div className="flex items-center gap-1">
                <button className="p-2.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors tooltip-trigger relative group">
                  <Search className="w-5 h-5" />
                  <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Pesquisar na base</span>
                </button>
                <button className="p-2.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors tooltip-trigger relative group">
                  <Paperclip className="w-5 h-5" />
                  <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Anexar arquivo</span>
                </button>
                <button className="p-2.5 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-xl transition-colors tooltip-trigger relative group">
                  <Mic className="w-5 h-5" />
                  <span className="absolute -top-8 left-1/2 -translate-x-1/2 bg-slate-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">Usar microfone</span>
                </button>
              </div>
              
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-slate-400 hidden sm:inline-block mr-2">
                  <kbd className="font-sans px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded-md">Enter</kbd> para enviar
                </span>
                <button className="flex items-center justify-center w-10 h-10 md:w-auto md:px-5 md:py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-medium shadow-md shadow-cyan-500/20 transition-all hover:shadow-cyan-500/40 active:scale-95 group">
                  <span className="hidden md:inline-block mr-2">Enviar</span>
                  <Send className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Conversations (Compact Row) */}
        <div className="w-full max-w-4xl mt-12 animate-in fade-in slide-in-from-bottom-8 duration-700 delay-300">
          <div className="flex items-center justify-between mb-4 px-2">
            <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Retomar Atividade
            </h3>
            <button className="text-xs font-medium text-cyan-600 hover:text-cyan-700 hover:underline">
              Ver histórico completo
            </button>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {RECENT_CHATS.map((chat) => (
              <button 
                key={chat.id}
                className="flex flex-col items-start p-4 rounded-2xl bg-white border border-slate-200 hover:border-cyan-300 hover:shadow-md hover:shadow-cyan-100/50 transition-all text-left group h-full"
              >
                <div className="w-8 h-8 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center mb-3 group-hover:bg-cyan-50 group-hover:border-cyan-100 transition-colors">
                  <MessageSquare className="w-4 h-4 text-slate-400 group-hover:text-cyan-500" />
                </div>
                <h4 className="text-sm font-semibold text-slate-700 leading-snug line-clamp-2 mb-1 group-hover:text-cyan-700 transition-colors">
                  {chat.title}
                </h4>
                <span className="text-xs text-slate-400 mt-auto font-medium">
                  {chat.time}
                </span>
              </button>
            ))}
          </div>
        </div>

      </main>

      {/* CSS for hiding scrollbar but keeping functionality */}
      <style dangerouslySetContent={{ __html: `
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}} />
    </div>
  );
}
