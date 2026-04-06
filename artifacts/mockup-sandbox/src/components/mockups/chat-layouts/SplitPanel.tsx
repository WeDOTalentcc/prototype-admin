import React from "react";
import { Brain, Search, Paperclip, Mic, Send, Clock, Briefcase, UserPlus, Calendar, Share2, FileSearch, CheckCircle, RefreshCcw, Settings } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Input } from "@/components/ui/input";

export function SplitPanel() {
  const suggestions = [
    { icon: Briefcase, text: "Crie uma nova vaga" },
    { icon: CheckCircle, text: "Solicite aprovação" },
    { icon: Share2, text: "Compartilhe candidatos" },
    { icon: Search, text: "Buscar candidatos" },
    { icon: FileSearch, text: "Consulte sobre candidato" },
    { icon: UserPlus, text: "Adicione novo candidato" },
    { icon: Calendar, text: "Reagende uma entrevista" },
    { icon: RefreshCcw, text: "Atualize status do candidato" },
  ];

  const recentChats = [
    { title: "Triagem: Engenheiro de Software Sênior", time: "Há 2 horas" },
    { title: "Agendamento: Maria Silva", time: "Ontem, 14:30" },
    { title: "Aprovação de Vaga: Designer de Produto", time: "24 de Out" },
    { title: "Busca: Desenvolvedor Frontend React", time: "22 de Out" },
  ];

  return (
    <div className="flex h-screen w-full bg-slate-50 text-slate-900 font-sans overflow-hidden">
      {/* Left Column - Navigation/Sidebar (35%) */}
      <div className="w-[35%] min-w-[320px] max-w-[400px] bg-white border-r border-slate-200 flex flex-col h-full z-10 shadow-sm">
        {/* Greeting Section */}
        <div className="p-6 border-b border-slate-100 bg-gradient-to-b from-slate-50 to-white">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-xl bg-cyan-100 flex items-center justify-center text-cyan-600 shadow-inner">
              <Brain size={24} />
            </div>
            <h1 className="text-2xl font-semibold tracking-tight text-slate-800">Oi, eu sou a LIA.</h1>
          </div>
          <p className="text-sm text-slate-500 leading-relaxed ml-1">
            Sua assistente inteligente de recrutamento. Como posso ajudar a otimizar seu dia hoje?
          </p>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          {/* Suggestions Rail */}
          <div className="p-6 pb-2">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 ml-1">Ações Rápidas</h2>
            <div className="flex flex-col gap-2">
              {suggestions.map((item, i) => (
                <button
                  key={i}
                  className="flex items-center gap-3 w-full text-left px-4 py-3 rounded-lg border border-slate-100 bg-white hover:bg-slate-50 hover:border-slate-200 transition-all group"
                >
                  <item.icon size={18} className="text-slate-400 group-hover:text-cyan-500 transition-colors" />
                  <span className="text-sm font-medium text-slate-600 group-hover:text-slate-800 transition-colors">{item.text}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Recent Conversations */}
          <div className="p-6 pt-4">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-4 ml-1">Conversas Recentes</h2>
            <div className="flex flex-col gap-1">
              {recentChats.map((chat, i) => (
                <button
                  key={i}
                  className="flex items-start gap-3 w-full text-left px-3 py-3 rounded-lg hover:bg-slate-50 transition-colors group"
                >
                  <div className="mt-0.5">
                    <Brain size={16} className="text-slate-300 group-hover:text-cyan-500" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 line-clamp-1">{chat.title}</span>
                    <span className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                      <Clock size={10} /> {chat.time}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right Column - Main Workspace (65%) */}
      <div className="flex-1 flex flex-col h-full relative bg-slate-50/50">
        {/* Top Bar - Controls */}
        <div className="absolute top-0 left-0 right-0 p-4 flex justify-end items-center gap-3 z-20">
          <Button variant="outline" size="sm" className="hidden sm:flex items-center gap-2 bg-white/80 backdrop-blur-sm border-slate-200 text-slate-600 hover:text-slate-900">
            <Search size={16} />
            <span className="text-xs">Buscar...</span>
          </Button>
          <Button variant="secondary" size="sm" className="bg-white/80 backdrop-blur-sm text-slate-700 border border-slate-200 hover:bg-slate-100 flex items-center gap-2 shadow-sm">
            <Settings size={16} className="text-slate-500" />
            <span className="text-sm font-medium">Centro de Controle</span>
          </Button>
          <Avatar className="h-9 w-9 border-2 border-white shadow-sm cursor-pointer">
            <AvatarFallback className="bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-medium">
              PM
            </AvatarFallback>
          </Avatar>
        </div>

        {/* Center Workspace */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 max-w-4xl mx-auto w-full relative">
          
          {/* Decorative background element */}
          <div className="absolute inset-0 flex items-center justify-center opacity-[0.02] pointer-events-none">
            <Brain size={400} />
          </div>

          <div className="w-full max-w-2xl relative z-10">
            <div className="mb-8 text-center">
              <h2 className="text-3xl font-bold text-slate-800 mb-3 tracking-tight">O que vamos resolver agora?</h2>
              <p className="text-slate-500">Descreva a tarefa, faça uma pergunta ou cole informações.</p>
            </div>

            {/* Prompt Input */}
            <div className="bg-white rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200/80 overflow-hidden ring-1 ring-black/[0.02] transition-all hover:shadow-2xl hover:shadow-cyan-100/20 hover:border-cyan-200/50 focus-within:shadow-2xl focus-within:shadow-cyan-100/30 focus-within:border-cyan-300">
              <div className="p-4 pb-2">
                <textarea
                  className="w-full min-h-[120px] resize-none bg-transparent text-slate-800 placeholder-slate-400 focus:outline-none text-base sm:text-lg leading-relaxed"
                  placeholder="Ex: Resuma os principais candidatos para a vaga de Designer de Produto..."
                />
              </div>
              <div className="px-4 py-3 bg-slate-50/80 border-t border-slate-100 flex justify-between items-center rounded-b-2xl">
                <div className="flex gap-1.5">
                  <Button variant="ghost" size="icon" className="h-9 w-9 text-slate-500 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors">
                    <Paperclip size={18} />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-9 w-9 text-slate-500 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors">
                    <Search size={18} />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-9 w-9 text-slate-500 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors">
                    <Mic size={18} />
                  </Button>
                </div>
                <Button className="bg-cyan-500 hover:bg-cyan-600 text-white rounded-full px-5 shadow-md shadow-cyan-500/20 transition-all hover:shadow-lg hover:shadow-cyan-500/30 hover:-translate-y-0.5 font-medium gap-2">
                  <span>Enviar</span>
                  <Send size={16} className="mt-0.5" />
                </Button>
              </div>
            </div>
            
            <div className="mt-6 text-center">
              <p className="text-xs text-slate-400 flex items-center justify-center gap-1.5">
                <Brain size={12} /> LIA pode cometer erros. Verifique informações importantes.
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #e2e8f0;
          border-radius: 10px;
        }
        .custom-scrollbar:hover::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
        }
      `}} />
    </div>
  );
}
