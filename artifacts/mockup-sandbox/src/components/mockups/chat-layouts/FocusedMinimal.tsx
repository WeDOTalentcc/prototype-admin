import React, { useState } from 'react';
import { 
  Brain, 
  Search, 
  Paperclip, 
  Mic, 
  Send, 
  ChevronDown, 
  Clock, 
  Sparkles,
  Briefcase,
  UserPlus,
  Users,
  UserCheck,
  Calendar,
  RefreshCw,
  MessageSquare
} from 'lucide-react';

export function FocusedMinimal() {
  const [isFocused, setIsFocused] = useState(false);
  const [showRecents, setShowRecents] = useState(false);

  const suggestions = [
    { icon: <Briefcase size={16} />, text: "Crie uma nova vaga" },
    { icon: <UserPlus size={16} />, text: "Solicite aprovação de nova vaga" },
    { icon: <Users size={16} />, text: "Compartilhe candidatos com gestor" },
    { icon: <Search size={16} />, text: "Buscar candidatos" },
    { icon: <UserCheck size={16} />, text: "Consulte sobre candidato" },
    { icon: <UserPlus size={16} />, text: "Adicione novo candidato" },
    { icon: <Calendar size={16} />, text: "Reagende uma entrevista" },
    { icon: <RefreshCw size={16} />, text: "Atualize status do candidato" },
  ];

  const recentChats = [
    { title: "Análise de currículos - Vaga Desenvolvedor Senior", time: "há 2 horas" },
    { title: "Agendamento de entrevistas - Vaga UX Designer", time: "há 5 horas" },
    { title: "Busca de candidatos - Vaga Product Manager", time: "ontem" },
  ];

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans relative flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex justify-between items-center p-6 w-full absolute top-0 left-0 z-10">
        <div className="flex items-center gap-2">
          {/* Recents Dropdown */}
          <div className="relative">
            <button 
              onClick={() => setShowRecents(!showRecents)}
              className="flex items-center gap-2 px-4 py-2 rounded-full hover:bg-zinc-100 transition-colors text-sm font-medium text-zinc-600"
            >
              <Clock size={16} />
              Recentes
              <ChevronDown size={14} className={`transition-transform ${showRecents ? 'rotate-180' : ''}`} />
            </button>
            
            {showRecents && (
              <div className="absolute top-full left-0 mt-2 w-80 bg-white border border-zinc-200 rounded-2xl shadow-xl overflow-hidden z-20">
                <div className="p-3">
                  <h3 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 px-3">Conversas Recentes</h3>
                  <div className="space-y-1">
                    {recentChats.map((chat, i) => (
                      <button key={i} className="w-full text-left flex items-start gap-3 p-3 rounded-xl hover:bg-zinc-50 transition-colors group">
                        <div className="bg-cyan-50 p-2 rounded-full text-cyan-600 group-hover:bg-cyan-100 transition-colors shrink-0">
                          <MessageSquare size={14} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-zinc-700 truncate">{chat.title}</p>
                          <p className="text-xs text-zinc-400 mt-0.5">{chat.time}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button className="flex items-center gap-2 px-5 py-2.5 bg-zinc-900 text-white rounded-full hover:bg-zinc-800 transition-colors text-sm font-medium shadow-sm">
            <Sparkles size={16} className="text-cyan-400" />
            Centro de Controle
          </button>
          <button className="w-10 h-10 flex items-center justify-center rounded-full border border-zinc-200 hover:bg-zinc-50 transition-colors">
            <Search size={18} className="text-zinc-600" />
          </button>
          <button className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 text-white font-medium flex items-center justify-center shadow-sm">
            N
          </button>
        </div>
      </header>

      {/* Main Content - Centered */}
      <main className="flex-1 flex flex-col items-center justify-center w-full max-w-3xl mx-auto px-6 relative z-0">
        
        {/* Greeting */}
        <div className={`flex flex-col items-center mb-8 transition-all duration-500 ${isFocused ? 'opacity-0 translate-y-4 pointer-events-none' : 'opacity-100 translate-y-0'}`}>
          <div className="w-12 h-12 bg-cyan-50 rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-cyan-100/50">
            <Brain size={24} className="text-cyan-500" />
          </div>
          <h1 className="text-lg font-medium text-zinc-500">
            Oi, sou a LIA. Como posso ajudar?
          </h1>
        </div>

        {/* Search/Prompt Container */}
        <div className={`w-full transition-all duration-500 ease-[cubic-bezier(0.23,1,0.32,1)] ${isFocused ? '-translate-y-12' : 'translate-y-0'}`}>
          
          <div className={`relative bg-white rounded-3xl transition-all duration-300 ${isFocused ? 'shadow-2xl border-cyan-500 ring-4 ring-cyan-500/10' : 'shadow-lg border-zinc-200 hover:border-zinc-300 hover:shadow-xl'} border`}>
            
            <textarea 
              className="w-full bg-transparent resize-none p-6 text-lg text-zinc-800 placeholder:text-zinc-400 focus:outline-none min-h-[120px] leading-relaxed"
              placeholder="Peça a LIA..."
              onFocus={() => setIsFocused(true)}
              onBlur={() => {
                // Small delay to allow clicking suggestions
                setTimeout(() => setIsFocused(false), 200);
              }}
            />

            <div className="flex items-center justify-between p-3 pt-0">
              <div className="flex items-center gap-1">
                <button className="w-10 h-10 flex items-center justify-center rounded-full text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors">
                  <Search size={20} />
                </button>
                <button className="w-10 h-10 flex items-center justify-center rounded-full text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors">
                  <Paperclip size={20} />
                </button>
                <button className="w-10 h-10 flex items-center justify-center rounded-full text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors">
                  <Mic size={20} />
                </button>
              </div>
              <button className={`w-12 h-12 flex items-center justify-center rounded-full transition-all duration-300 ${isFocused ? 'bg-cyan-500 text-white shadow-md hover:bg-cyan-600 hover:shadow-lg scale-105' : 'bg-zinc-100 text-zinc-400 hover:bg-zinc-200'}`}>
                <Send size={20} className={isFocused ? 'ml-1' : ''} />
              </button>
            </div>
          </div>

          {/* Autocomplete Suggestions */}
          <div className={`absolute left-0 right-0 mt-4 transition-all duration-500 ${isFocused ? 'opacity-100 translate-y-0 visible' : 'opacity-0 -translate-y-4 invisible'}`}>
            <div className="bg-white border border-zinc-100 rounded-3xl shadow-xl p-3">
              <div className="flex items-center justify-between px-4 py-2 mb-2">
                <span className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Sugestões de Ações</span>
                <span className="text-xs text-zinc-400 bg-zinc-100 px-2 py-1 rounded-md">Tab para navegar</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                {suggestions.map((suggestion, index) => (
                  <button 
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-2xl hover:bg-zinc-50 text-left transition-colors group border border-transparent hover:border-zinc-100"
                  >
                    <div className="w-8 h-8 rounded-full bg-zinc-100 flex items-center justify-center text-zinc-500 group-hover:bg-cyan-50 group-hover:text-cyan-600 transition-colors">
                      {suggestion.icon}
                    </div>
                    <span className="text-sm font-medium text-zinc-600 group-hover:text-zinc-900">{suggestion.text}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>

        </div>
      </main>

      {/* Floating Action Button */}
      <button className="absolute bottom-6 left-6 w-14 h-14 bg-cyan-500 text-white rounded-full flex items-center justify-center shadow-lg shadow-cyan-500/30 hover:bg-cyan-600 hover:scale-105 hover:shadow-xl hover:shadow-cyan-500/40 transition-all duration-300 z-10 group">
        <Brain size={24} className="group-hover:animate-pulse" />
      </button>

    </div>
  );
}
