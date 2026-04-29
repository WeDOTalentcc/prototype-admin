import React, { useState } from 'react';
import './_group.css';
import {
  Brain,
  Plus,
  Search,
  UserCheck,
  Calendar,
  RefreshCcw,
  Mic,
  Send,
  Paperclip
} from 'lucide-react';

export default function TighterRhythm() {
  const [inputValue, setInputValue] = useState('');
  
  const suggestions = [
    {
      icon: <Plus className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Crie uma nova vaga',
      description: 'Configure requisitos com descrição detalhada',
    },
    {
      icon: <Search className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Buscar candidatos',
      description: 'Encontre candidatos por perfil, skills ou experiência',
    },
    {
      icon: <Search className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Consulte sobre candidato',
      description: 'Obtenha histórico específico e completo',
    },
    {
      icon: <UserCheck className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Adicione novo candidato',
      description: 'Cadastre perfil com talentos',
    },
    {
      icon: <Calendar className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Reagende uma entrevista',
      description: 'Cancele horário e notifique participantes',
    },
    {
      icon: <RefreshCcw className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: 'Atualize status do candidato',
      description: 'Modifique situação e envie notificações',
    },
  ];

  return (
    <div 
      className="min-h-[100dvh] w-full flex flex-col items-center justify-center p-6"
      style={{ backgroundColor: 'var(--lia-bg-secondary)', fontFamily: "'Open Sans', sans-serif" }}
    >
      <div className="w-full max-w-3xl mx-auto flex flex-col items-center justify-center h-full pt-[10vh]">
        
        {/* Header Section - Tighter Rhythm */}
        <div className="flex flex-col items-center mb-8 text-center">
          <div className="flex items-center gap-3 mb-1">
            <Brain className="w-9 h-9" style={{ color: 'var(--wedo-cyan)' }} />
            <h1 className="text-[32px] tracking-tight text-[var(--lia-text-primary)] font-light">
              Oi, eu sou a <span style={{ fontFamily: "'Source Serif 4', serif" }} className="font-bold">LIA.</span>
            </h1>
          </div>
          <p className="text-[14px] text-[var(--lia-text-secondary)] font-medium">
            Como posso ajudar você hoje?
          </p>
        </div>

        {/* Cards Section - Tightened gap below */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full mb-8">
          {suggestions.map((item, index) => (
            <button
              key={index}
              onClick={() => setInputValue(item.title)}
              className="flex items-start text-left p-4 rounded-xl border border-[var(--lia-border-subtle)] bg-[var(--lia-bg-elevated)] hover:bg-[var(--lia-interactive-hover)] hover:border-[var(--wedo-cyan-light)] transition-all group shadow-[var(--lia-shadow-sm)] hover:shadow-[var(--lia-shadow-default)]"
            >
              <div className="flex-shrink-0 p-2.5 rounded-lg bg-[#60BED1]/10 mr-4 group-hover:bg-[#60BED1]/20 transition-colors">
                {item.icon}
              </div>
              <div className="flex flex-col pt-0.5">
                <span className="text-[14px] font-semibold text-[var(--lia-text-primary)] mb-0.5">
                  {item.title}
                </span>
                <span className="text-[12px] text-[var(--lia-text-secondary)] leading-[1.4]">
                  {item.description}
                </span>
              </div>
            </button>
          ))}
        </div>

        {/* Input Section - Wider, slimmer, tighter grouping */}
        <div className="w-full relative shadow-[var(--lia-shadow-default)] rounded-2xl bg-[var(--lia-bg-elevated)] border border-[var(--lia-border-default)] transition-all focus-within:border-[#60BED1] focus-within:ring-1 focus-within:ring-[#60BED1] focus-within:shadow-[0_0_15px_rgba(96,190,209,0.15)]">
          <div className="flex items-center p-1.5 min-h-[56px]">
            <button className="p-2.5 mx-1 text-[var(--lia-text-secondary)] hover:text-[var(--wedo-cyan)] transition-colors rounded-full hover:bg-[var(--lia-interactive-hover)]">
              <Search className="w-[18px] h-[18px]" />
            </button>
            
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Peça a LIA..."
              className="flex-1 bg-transparent border-none outline-none px-2 text-[15px] text-[var(--lia-text-primary)] placeholder:text-[var(--lia-text-tertiary)]"
              onKeyDown={(e) => {
                if (e.key === 'Enter' && inputValue.trim()) {
                  setInputValue('');
                }
              }}
            />
            
            <div className="flex items-center gap-1 pr-1.5">
              <button className="p-2.5 text-[var(--lia-text-secondary)] hover:text-[var(--wedo-cyan)] transition-colors rounded-full hover:bg-[var(--lia-interactive-hover)]">
                <Paperclip className="w-[18px] h-[18px]" />
              </button>
              <button className="p-2.5 text-[var(--lia-text-secondary)] hover:text-[var(--wedo-cyan)] transition-colors rounded-full hover:bg-[var(--lia-interactive-hover)]">
                <Mic className="w-[18px] h-[18px]" />
              </button>
              <button 
                onClick={() => setInputValue('')}
                disabled={!inputValue.trim()}
                className={`p-2.5 ml-1 rounded-xl transition-all flex items-center justify-center ${
                  inputValue.trim() 
                    ? 'bg-[var(--wedo-cyan)] text-white hover:bg-[var(--wedo-cyan-dark)] shadow-[0_2px_8px_rgba(96,190,209,0.3)]' 
                    : 'bg-[var(--lia-bg-tertiary)] text-[var(--lia-text-disabled)]'
                }`}
              >
                <Send className="w-[18px] h-[18px]" />
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
