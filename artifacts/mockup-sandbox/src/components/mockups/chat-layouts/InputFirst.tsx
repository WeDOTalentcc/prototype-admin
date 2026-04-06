import React from "react";
import { Brain, Search, Paperclip, Mic, Send, Cpu, Clock, ArrowRight } from "lucide-react";
import { Button } from "../../ui/button";
import { Textarea } from "../../ui/textarea";

export function InputFirst() {
  const suggestions = [
    "Crie uma nova vaga",
    "Solicite aprovação",
    "Compartilhe candidatos",
    "Buscar candidatos",
    "Consulte sobre candidato",
    "Adicione novo candidato",
    "Reagende uma entrevista",
    "Atualize status do candidato"
  ];

  const recentConversations = [
    { title: "Análise de perfil para Desenvolvedor Senior", time: "Há 2 horas" },
    { title: "Triagem de candidatos - Vaga de Marketing", time: "Ontem" },
    { title: "Agendamento de entrevistas com finalistas", time: "Segunda-feira" },
  ];

  return (
    <div className="flex h-screen bg-slate-50 flex-col text-slate-900 font-sans overflow-hidden">
      {/* Top Bar */}
      <header className="flex justify-between items-center px-6 py-4 bg-transparent absolute top-0 left-0 right-0 z-10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-cyan-100 flex items-center justify-center text-cyan-600">
            <Brain className="w-5 h-5" />
          </div>
          <span className="font-semibold text-lg tracking-tight">LIA</span>
        </div>
        
        <div className="flex items-center gap-4">
          <Button variant="outline" size="sm" className="hidden md:flex gap-2 bg-white/50 backdrop-blur-sm border-gray-200">
            <Cpu className="w-4 h-4" />
            Centro de Controle
          </Button>
          <Button variant="ghost" size="icon" className="text-gray-500 bg-white/50 backdrop-blur-sm rounded-full">
            <Search className="w-5 h-5" />
          </Button>
          <div className="w-9 h-9 rounded-full bg-cyan-600 flex items-center justify-center text-white font-medium shadow-sm">
            F
          </div>
        </div>
      </header>

      {/* Main Scrollable Content */}
      <main className="flex-1 overflow-y-auto pt-24 pb-12 px-4 flex flex-col items-center">
        
        <div className="w-full max-w-3xl mx-auto flex flex-col items-center mt-[10vh] mb-[10vh] shrink-0">
          {/* Greeting - Minimal */}
          <div className="text-center mb-8">
            <h1 className="text-3xl md:text-4xl font-medium text-slate-800 mb-3 tracking-tight">Oi, eu sou a LIA.</h1>
            <p className="text-slate-500 text-lg">Como posso ajudar na sua jornada de recrutamento hoje?</p>
          </div>

          {/* Hero Input Area */}
          <div className="w-full bg-white rounded-3xl shadow-[0_8px_40px_rgb(0,0,0,0.08)] border border-gray-200 overflow-hidden transition-all focus-within:shadow-[0_8px_40px_rgb(6,182,212,0.15)] focus-within:border-cyan-300">
            <Textarea 
              placeholder="Faça uma pergunta ou dê um comando..." 
              className="min-h-[140px] resize-none border-0 focus-visible:ring-0 px-6 py-6 text-xl placeholder:text-gray-400 bg-transparent"
            />
            <div className="flex items-center justify-between px-4 py-3 bg-white">
              <div className="flex items-center gap-1">
                <Button variant="ghost" size="icon" className="text-gray-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full h-10 w-10">
                  <Search className="w-5 h-5" />
                </Button>
                <Button variant="ghost" size="icon" className="text-gray-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full h-10 w-10">
                  <Paperclip className="w-5 h-5" />
                </Button>
                <Button variant="ghost" size="icon" className="text-gray-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full h-10 w-10">
                  <Mic className="w-5 h-5" />
                </Button>
              </div>
              <Button className="bg-cyan-500 hover:bg-cyan-600 text-white rounded-full px-6 h-10 shadow-sm gap-2 font-medium">
                Enviar <Send className="w-4 h-4 ml-1" />
              </Button>
            </div>
          </div>
        </div>

        <div className="w-full max-w-4xl mx-auto flex flex-col gap-12 pb-12">
          {/* Discovery Tiles / Suggestions */}
          <div className="w-full">
            <div className="flex items-center mb-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest">Ações Rápidas</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {suggestions.map((suggestion, idx) => (
                <button 
                  key={idx}
                  className="text-left p-5 rounded-2xl bg-white border border-gray-100 hover:border-cyan-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 group flex flex-col justify-between min-h-[120px]"
                >
                  <span className="text-sm font-medium text-slate-700 group-hover:text-cyan-800 leading-snug">{suggestion}</span>
                  <ArrowRight className="w-4 h-4 text-cyan-500 self-end opacity-0 group-hover:opacity-100 transform -translate-x-2 group-hover:translate-x-0 transition-all duration-300" />
                </button>
              ))}
            </div>
          </div>

          {/* Recent Conversations */}
          <div className="w-full">
            <div className="flex items-center mb-6">
              <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                <Clock className="w-4 h-4" /> Recentes
              </h2>
            </div>
            <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
              {recentConversations.map((conv, idx) => (
                <button 
                  key={idx}
                  className={`w-full text-left px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors group ${idx !== recentConversations.length - 1 ? 'border-b border-gray-50' : ''}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-400 group-hover:text-cyan-600 group-hover:bg-cyan-50 group-hover:border-cyan-100 transition-colors shrink-0">
                      <Brain className="w-4 h-4" />
                    </div>
                    <span className="text-sm font-medium text-slate-700 group-hover:text-cyan-800 transition-colors truncate">{conv.title}</span>
                  </div>
                  <span className="text-xs text-slate-400 whitespace-nowrap ml-4">{conv.time}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
