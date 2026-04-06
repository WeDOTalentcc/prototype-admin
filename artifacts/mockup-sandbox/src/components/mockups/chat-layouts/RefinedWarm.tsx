import React, { useState } from "react"
import {
  Brain,
  Search,
  Paperclip,
  Mic,
  Send,
  Cpu,
  Plus,
  FileText,
  UserCheck,
  Calendar,
  RefreshCcw,
  Clock
} from "lucide-react"

const SUGGESTIONS = [
  {
    icon: Plus,
    title: "Crie uma nova vaga",
    category: "vagas",
    colorClass: "border-cyan-400 text-cyan-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-cyan-50/50 hover:to-transparent"
  },
  {
    icon: FileText,
    title: "Solicite aprovacao de nova vaga",
    category: "vagas",
    colorClass: "border-cyan-400 text-cyan-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-cyan-50/50 hover:to-transparent"
  },
  {
    icon: UserCheck,
    title: "Compartilhe candidatos com gestor",
    category: "candidatos",
    colorClass: "border-green-400 text-green-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-green-50/50 hover:to-transparent"
  },
  {
    icon: Search,
    title: "Buscar candidatos",
    category: "candidatos",
    colorClass: "border-green-400 text-green-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-green-50/50 hover:to-transparent"
  },
  {
    icon: Search,
    title: "Consulte sobre candidato",
    category: "candidatos",
    colorClass: "border-green-400 text-green-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-green-50/50 hover:to-transparent"
  },
  {
    icon: UserCheck,
    title: "Adicione novo candidato",
    category: "candidatos",
    colorClass: "border-green-400 text-green-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-green-50/50 hover:to-transparent"
  },
  {
    icon: Calendar,
    title: "Reagende uma entrevista",
    category: "entrevistas",
    colorClass: "border-amber-400 text-amber-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-amber-50/50 hover:to-transparent"
  },
  {
    icon: RefreshCcw,
    title: "Atualize status do candidato",
    category: "candidatos",
    colorClass: "border-green-400 text-green-700",
    bgHoverClass: "hover:bg-gradient-to-r hover:from-green-50/50 hover:to-transparent"
  }
]

const RECENTS = [
  { title: "Analise de curriculos para Desenvolvedor Frontend", time: "Ha 2 horas" },
  { title: "Criacao de vaga para Designer UX/UI", time: "Ontem" },
  { title: "Agendamento de entrevista com Joao Silva", time: "Ha 2 dias" }
]

export function RefinedWarm() {
  const [prompt, setPrompt] = useState("")

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans relative">
      {/* Top Header */}
      <header className="absolute top-0 w-full p-4 flex justify-end items-center gap-3">
        <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-full shadow-sm text-sm font-medium text-slate-700 hover:bg-slate-50 transition-all duration-200">
          <Cpu className="w-4 h-4 text-slate-500" />
          Centro de Controle
        </button>
        <button className="p-2 bg-white border border-slate-200 rounded-full shadow-sm text-slate-500 hover:bg-slate-50 transition-all duration-200">
          <Search className="w-4 h-4" />
        </button>
        <div className="w-8 h-8 rounded-full bg-cyan-600 flex items-center justify-center text-white font-medium shadow-sm">
          N
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 max-w-3xl mx-auto w-full pt-20 pb-24">
        
        {/* Greeting Area */}
        <div className="flex flex-col items-center mb-10">
          <div className="bg-cyan-50 rounded-2xl p-4 shadow-[0_4px_20px_-4px_rgba(6,182,212,0.1)] mb-4">
            <Brain className="w-8 h-8 text-cyan-500" />
          </div>
          <h1 className="text-3xl font-semibold text-slate-800 mb-2">
            Oi, eu sou a <span className="font-serif text-cyan-600">LIA</span>.
          </h1>
          <p className="text-slate-500 text-lg">Como posso ajudar voce hoje?</p>
        </div>

        {/* Suggestion Cards */}
        <div className="w-full mb-10">
          <h2 className="text-xs uppercase tracking-wide text-slate-400 font-semibold mb-4 ml-1">O que posso fazer</h2>
          <div className="grid grid-cols-2 gap-3">
            {SUGGESTIONS.map((s, i) => {
              const Icon = s.icon
              return (
                <button
                  key={i}
                  className={`flex items-center gap-3 p-3 bg-white border border-slate-200 rounded-xl shadow-sm text-left transition-all duration-200 border-l-[3px] ${s.colorClass.split(" ")[0]} ${s.bgHoverClass} hover:shadow-md hover:-translate-y-0.5 group`}
                >
                  <Icon className={`w-4 h-4 ${s.colorClass.split(" ")[1]}`} />
                  <span className="text-sm font-medium text-slate-700 group-hover:text-slate-900 transition-colors">
                    {s.title}
                  </span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Prompt Input */}
        <div className="w-full bg-white rounded-2xl border border-slate-200 shadow-[0_8px_30px_-4px_rgba(148,163,184,0.2)] p-4 transition-all duration-200 hover:shadow-[0_8px_30px_-4px_rgba(148,163,184,0.3)] focus-within:shadow-[0_8px_30px_-4px_rgba(6,182,212,0.15)] focus-within:border-cyan-300 relative z-10">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Peca a LIA..."
            className="w-full bg-transparent border-none outline-none resize-none min-h-[60px] text-slate-700 placeholder:text-slate-400 text-base"
            rows={2}
          />
          <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100/50">
            <div className="flex items-center gap-1">
              <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors duration-200">
                <Search className="w-4 h-4" />
              </button>
              <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors duration-200">
                <Paperclip className="w-4 h-4" />
              </button>
              <button className="p-2 text-slate-400 hover:text-cyan-600 hover:bg-cyan-50 rounded-full transition-colors duration-200">
                <Mic className="w-4 h-4" />
              </button>
            </div>
            <button 
              className={`p-2.5 rounded-full transition-all duration-200 ${
                prompt.length > 0 
                  ? 'bg-cyan-500 text-white hover:bg-cyan-600 shadow-md hover:shadow-lg' 
                  : 'bg-slate-100 text-slate-400'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="w-full h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent my-10 opacity-70"></div>

        {/* Recent Conversations */}
        <div className="w-full">
          <div className="flex items-center justify-between mb-4 px-1">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Clock className="w-4 h-4 text-slate-400" />
              Recentes
            </h2>
            <button className="text-xs font-medium text-slate-400 hover:text-cyan-600 transition-colors duration-200">
              Limpar recentes
            </button>
          </div>
          <div className="space-y-2">
            {RECENTS.map((r, i) => (
              <button key={i} className="w-full flex items-center justify-between p-3 bg-white border border-slate-100 rounded-xl hover:bg-slate-50 hover:border-slate-200 transition-all duration-200 group">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 opacity-70 group-hover:opacity-100 transition-opacity"></div>
                  <span className="text-sm text-slate-600 group-hover:text-slate-900 transition-colors">{r.title}</span>
                </div>
                <span className="text-xs text-slate-400">{r.time}</span>
              </button>
            ))}
          </div>
        </div>
      </main>

      {/* Floating Brain Icon */}
      <button className="fixed bottom-6 left-6 p-3 bg-white rounded-2xl shadow-[0_8px_30px_-4px_rgba(148,163,184,0.3)] border border-slate-100 hover:shadow-[0_8px_30px_-4px_rgba(6,182,212,0.2)] hover:-translate-y-1 transition-all duration-300 group z-50">
        <Brain className="w-6 h-6 text-cyan-500 group-hover:scale-110 transition-transform duration-300" />
      </button>

    </div>
  )
}
