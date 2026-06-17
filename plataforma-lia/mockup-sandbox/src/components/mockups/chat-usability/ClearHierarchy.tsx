import React, { useState } from 'react';
import { Brain, Plus, Search, UserCheck, Calendar, RefreshCcw, Mic, Send, Paperclip } from 'lucide-react';
import './_group.css';

export default function ClearHierarchy() {
  const [inputValue, setInputValue] = useState('');

  const suggestions = [
    {
      icon: <Plus className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Crie uma nova vaga",
      description: "Configure requisitos com descrição detalhada"
    },
    {
      icon: <Search className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Buscar candidatos",
      description: "Encontre candidatos por perfil, skills ou experiência"
    },
    {
      icon: <Search className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Consulte sobre candidato",
      description: "Obtenha histórico específico e completo"
    },
    {
      icon: <UserCheck className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Adicione novo candidato",
      description: "Cadastre perfil com talentos"
    },
    {
      icon: <Calendar className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Reagende uma entrevista",
      description: "Cancele horário e notifique participantes"
    },
    {
      icon: <RefreshCcw className="w-5 h-5 text-[var(--wedo-cyan)]" />,
      title: "Atualize status do candidato",
      description: "Modifique situação e envie notificações"
    }
  ];

  return (
    <div className="min-h-screen bg-[var(--lia-bg-primary)] flex flex-col items-center justify-center p-4 sm:p-8" style={{ fontFamily: "'Open Sans', sans-serif" }}>
      
      {/* Main Content Container */}
      <div className="w-full max-w-4xl flex flex-col items-center gap-16 w-full flex-grow pt-16">
        
        {/* Tier 1: Dominant Greeting */}
        <div className="flex flex-col items-center text-center space-y-6 max-w-2xl">
          <div className="p-4 bg-[var(--wedo-cyan-light)] bg-opacity-20 rounded-full mb-2">
            <Brain className="w-12 h-12 text-[var(--wedo-cyan)]" />
          </div>
          <div>
            <h1 className="text-[32px] sm:text-[40px] text-[var(--lia-text-primary)] leading-tight tracking-tight">
              <span className="font-semibold font-['Open_Sans']">Oi, eu sou a </span>
              <span className="font-bold text-[40px] sm:text-[48px] text-[var(--wedo-cyan-dark)]" style={{ fontFamily: "'Source Serif 4', serif" }}>LIA.</span>
            </h1>
            <p className="text-[16px] sm:text-[18px] text-[var(--lia-text-secondary)] mt-4 font-medium">
              Como posso ajudar você hoje?
            </p>
          </div>
        </div>

        {/* Tier 2: Secondary Discovery Zone */}
        <div className="w-full max-w-3xl flex flex-col gap-6">
          <div className="flex items-center gap-4">
            <div className="h-[1px] flex-grow bg-[var(--lia-border-subtle)]"></div>
            <h2 className="text-[13px] font-semibold text-[var(--lia-text-tertiary)] uppercase tracking-wider px-2">
              O que posso fazer por você
            </h2>
            <div className="h-[1px] flex-grow bg-[var(--lia-border-subtle)]"></div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {suggestions.map((item, idx) => (
              <button 
                key={idx}
                className="group flex items-start gap-4 p-5 rounded-xl border border-[var(--lia-border-subtle)] bg-[var(--lia-bg-primary)] hover:bg-[var(--lia-interactive-hover)] hover:border-[var(--lia-border-default)] transition-all duration-200 text-left shadow-[var(--lia-shadow-sm)] hover:shadow-[var(--lia-shadow-default)]"
              >
                <div className="flex-shrink-0 p-2.5 rounded-lg bg-[var(--wedo-cyan)] bg-opacity-10 group-hover:bg-opacity-20 transition-colors">
                  {item.icon}
                </div>
                <div className="flex flex-col gap-1">
                  <h3 className="text-[15px] font-semibold text-[var(--lia-text-primary)] group-hover:text-[var(--wedo-cyan-dark)] transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-[13px] text-[var(--lia-text-secondary)] leading-relaxed">
                    {item.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Tier 3: Tertiary Action Zone (Input) */}
      <div className="w-full max-w-3xl mt-12 mb-8">
        <div className="relative group">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-[var(--lia-text-tertiary)] group-focus-within:text-[var(--wedo-cyan)] transition-colors" />
          </div>
          
          <textarea 
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Peça a LIA..."
            className="w-full min-h-[60px] max-h-[120px] bg-[var(--lia-bg-secondary)] border border-[var(--lia-border-subtle)] rounded-xl py-4 pl-11 pr-32 text-[14px] text-[var(--lia-text-primary)] placeholder-[var(--lia-text-tertiary)] focus:outline-none focus:ring-1 focus:ring-[var(--wedo-cyan)] focus:border-[var(--wedo-cyan)] focus:bg-[var(--lia-bg-primary)] transition-all resize-none shadow-none"
            style={{ 
              scrollbarWidth: 'none',
              msOverflowStyle: 'none'
            }}
          />
          
          <div className="absolute bottom-3 right-3 flex items-center gap-1">
            <button className="p-2 text-[var(--lia-text-tertiary)] hover:text-[var(--lia-text-primary)] hover:bg-[var(--lia-interactive-hover)] rounded-lg transition-colors">
              <Paperclip className="w-4 h-4" />
            </button>
            <button className="p-2 text-[var(--lia-text-tertiary)] hover:text-[var(--lia-text-primary)] hover:bg-[var(--lia-interactive-hover)] rounded-lg transition-colors">
              <Mic className="w-4 h-4" />
            </button>
            <button 
              className={`p-2 rounded-lg transition-colors ml-1 ${
                inputValue.trim() 
                  ? 'bg-[var(--wedo-cyan)] text-white hover:bg-[var(--wedo-cyan-dark)]' 
                  : 'bg-[var(--lia-bg-tertiary)] text-[var(--lia-text-disabled)]'
              }`}
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        <p className="text-center text-[11px] text-[var(--lia-text-tertiary)] mt-3">
          A LIA pode cometer erros. Considere verificar informações importantes.
        </p>
      </div>

    </div>
  );
}
