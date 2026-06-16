import React, { useState } from 'react';
import { 
  Brain, 
  Plus, 
  Search, 
  UserCheck, 
  Calendar, 
  RefreshCcw, 
  Mic, 
  Send, 
  Paperclip,
  ChevronRight
} from 'lucide-react';
import './_group.css';

export function StrongAffordance() {
  const [inputText, setInputText] = useState('');

  const cards = [
    {
      icon: <Plus className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Crie uma nova vaga",
      description: "Configure requisitos com descrição detalhada"
    },
    {
      icon: <Search className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Buscar candidatos",
      description: "Encontre candidatos por perfil, skills ou experiência"
    },
    {
      icon: <Search className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Consulte sobre candidato",
      description: "Obtenha histórico específico e completo"
    },
    {
      icon: <UserCheck className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Adicione novo candidato",
      description: "Cadastre perfil com talentos"
    },
    {
      icon: <Calendar className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Reagende uma entrevista",
      description: "Cancele horário e notifique participantes"
    },
    {
      icon: <RefreshCcw className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />,
      title: "Atualize status do candidato",
      description: "Modifique situação e envie notificações"
    }
  ];

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 md:p-8"
      style={{ 
        backgroundColor: 'var(--lia-bg-secondary)', 
        fontFamily: "'Open Sans', sans-serif",
        color: 'var(--lia-text-primary)'
      }}
    >
      <div className="max-w-4xl w-full flex flex-col h-full gap-8">
        
        {/* Header Section */}
        <div className="flex flex-col items-center text-center mt-12 mb-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center shadow-sm" style={{ backgroundColor: 'var(--lia-bg-elevated)', border: '1px solid var(--lia-border-subtle)' }}>
              <Brain className="w-6 h-6" style={{ color: 'var(--wedo-cyan)' }} />
            </div>
            <h1 className="text-2xl font-semibold flex items-baseline gap-2">
              Oi, eu sou a
              <span style={{ fontFamily: "'Source Serif 4', serif", fontWeight: 700, color: 'var(--wedo-cyan)' }}>LIA.</span>
            </h1>
          </div>
          <p className="text-sm font-medium px-4 py-1.5 rounded-full" style={{ backgroundColor: 'var(--lia-bg-elevated)', color: 'var(--lia-text-secondary)', border: '1px solid var(--lia-border-subtle)' }}>
            Como posso ajudar você hoje?
          </p>
        </div>

        {/* Suggestion Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full flex-grow">
          {cards.map((card, index) => (
            <button
              key={index}
              className="group flex items-start gap-4 p-5 rounded-2xl text-left transition-all duration-200 outline-none focus-visible:ring-4 focus-visible:ring-offset-2"
              style={{
                backgroundColor: 'var(--lia-bg-elevated)',
                border: '2px solid var(--lia-border-subtle)',
                boxShadow: 'var(--lia-shadow-sm)',
                '--tw-ring-color': 'var(--wedo-cyan-light)'
              } as React.CSSProperties}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = 'var(--wedo-cyan)';
                e.currentTarget.style.backgroundColor = '#F0FAFC';
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = 'var(--lia-shadow-md)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = 'var(--lia-border-subtle)';
                e.currentTarget.style.backgroundColor = 'var(--lia-bg-elevated)';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'var(--lia-shadow-sm)';
              }}
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center transition-colors" style={{ backgroundColor: 'var(--wedo-cyan-light)' }}>
                {card.icon}
              </div>
              <div className="flex flex-col flex-grow">
                <span className="font-semibold text-base mb-1" style={{ color: 'var(--lia-text-primary)' }}>
                  {card.title}
                </span>
                <span className="text-sm leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>
                  {card.description}
                </span>
              </div>
              <div className="flex-shrink-0 self-center ml-2 w-8 h-8 rounded-full flex items-center justify-center opacity-40 group-hover:opacity-100 group-hover:bg-white transition-all duration-200">
                <ChevronRight className="w-5 h-5" style={{ color: 'var(--wedo-cyan)' }} />
              </div>
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="mt-auto pt-8 pb-4 w-full">
          <label htmlFor="lia-input" className="block text-sm font-semibold mb-2 ml-2" style={{ color: 'var(--lia-text-primary)' }}>
            Digite sua mensagem
          </label>
          <div 
            className="flex flex-col bg-white rounded-2xl overflow-hidden focus-within:ring-4 focus-within:ring-offset-0 transition-all"
            style={{ 
              border: '2px solid var(--wedo-cyan-light)',
              boxShadow: '0 4px 12px rgba(96, 190, 209, 0.1)',
              '--tw-ring-color': 'var(--wedo-cyan-light)'
            } as React.CSSProperties}
          >
            <textarea
              id="lia-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Peça a LIA..."
              className="w-full min-h-[100px] p-4 resize-none outline-none text-base bg-transparent"
              style={{ color: 'var(--lia-text-primary)' }}
            />
            <div className="flex items-center justify-between p-3" style={{ borderTop: '1px solid var(--lia-border-subtle)', backgroundColor: 'var(--lia-bg-tertiary)' }}>
              <div className="flex items-center gap-2">
                <button 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white transition-colors text-sm font-medium outline-none focus-visible:ring-2"
                  style={{ color: 'var(--lia-text-secondary)', '--tw-ring-color': 'var(--wedo-cyan)' } as React.CSSProperties}
                >
                  <Paperclip className="w-4 h-4" />
                  <span>Anexar</span>
                </button>
                <button 
                  className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white transition-colors text-sm font-medium outline-none focus-visible:ring-2"
                  style={{ color: 'var(--lia-text-secondary)', '--tw-ring-color': 'var(--wedo-cyan)' } as React.CSSProperties}
                >
                  <Mic className="w-4 h-4" />
                  <span>Gravar</span>
                </button>
              </div>
              <button 
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold transition-all transform active:scale-95 outline-none focus-visible:ring-4 focus-visible:ring-offset-2"
                style={{ 
                  backgroundColor: inputText.length > 0 ? 'var(--wedo-cyan)' : 'var(--wedo-cyan-light)',
                  color: inputText.length > 0 ? 'white' : 'var(--lia-text-secondary)',
                  opacity: inputText.length > 0 ? 1 : 0.8,
                  '--tw-ring-color': 'var(--wedo-cyan)'
                } as React.CSSProperties}
                disabled={inputText.length === 0}
              >
                <span>Enviar</span>
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          {/* Tradeoff Explanation */}
          <div className="mt-6 p-4 rounded-xl text-xs flex items-start gap-3" style={{ backgroundColor: 'var(--lia-bg-elevated)', border: '1px dashed var(--lia-border-default)', color: 'var(--lia-text-secondary)' }}>
            <div className="font-bold uppercase tracking-wider text-[10px]" style={{ color: 'var(--wedo-orange)' }}>Tradeoff</div>
            <p>
              More affordance signals = more visual noise. The interface feels busier and less minimal. Elements like arrows and labels take up space and can feel redundant to experienced users. This is the cost of making everything discoverable.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
}
