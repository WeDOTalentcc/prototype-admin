import React from 'react';
import { Brain, Plus, Search, UserCheck, Calendar, RefreshCcw, Mic, Send, Paperclip } from 'lucide-react';
import './_group.css';

export function ElevatedCards() {
  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center p-4 md:p-8"
      style={{ 
        backgroundColor: 'var(--lia-bg-primary)',
        fontFamily: "'Open Sans', sans-serif",
        color: 'var(--lia-text-primary)'
      }}
    >
      <div className="w-full max-w-3xl flex flex-col items-center mb-10">
        <div className="mb-6">
          <Brain 
            size={40} 
            strokeWidth={1.5}
            style={{ color: 'var(--wedo-cyan)' }}
          />
        </div>
        <h1 className="text-3xl md:text-4xl font-light tracking-tight mb-3 text-center">
          Oi, eu sou a <span style={{ fontFamily: "'Source Serif 4', serif", fontWeight: 700 }}>LIA.</span>
        </h1>
        <p className="text-lg md:text-xl text-center" style={{ color: 'var(--lia-text-secondary)' }}>
          Como posso ajudar você hoje?
        </p>
      </div>

      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {/* Card 1 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'var(--wedo-cyan-light)', color: 'var(--wedo-cyan-dark)' }}>
            <Plus size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Crie uma nova vaga</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Configure requisitos com descrição detalhada</p>
          </div>
        </button>

        {/* Card 2 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(93, 164, 122, 0.15)', color: 'var(--wedo-green)' }}>
            <Search size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Buscar candidatos</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Encontre candidatos por perfil, skills ou experiência</p>
          </div>
        </button>

        {/* Card 3 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(93, 164, 122, 0.15)', color: 'var(--wedo-green)' }}>
            <Search size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Consulte sobre candidato</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Obtenha histórico específico e completo</p>
          </div>
        </button>

        {/* Card 4 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(93, 164, 122, 0.15)', color: 'var(--wedo-green)' }}>
            <UserCheck size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Adicione novo candidato</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Cadastre perfil com talentos</p>
          </div>
        </button>

        {/* Card 5 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(209, 153, 96, 0.15)', color: 'var(--wedo-orange)' }}>
            <Calendar size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Reagende uma entrevista</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Cancele horário e notifique participantes</p>
          </div>
        </button>

        {/* Card 6 */}
        <button 
          className="flex items-start text-left p-5 rounded-xl border transition-all duration-200 hover:-translate-y-1 bg-white"
          style={{ 
            borderColor: 'var(--lia-border-subtle)',
            boxShadow: 'var(--lia-shadow-sm)'
          }}
        >
          <div className="flex-shrink-0 mr-4 p-3 rounded-lg" style={{ backgroundColor: 'rgba(93, 164, 122, 0.15)', color: 'var(--wedo-green)' }}>
            <RefreshCcw size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-[15px] mb-1">Atualize status do candidato</h3>
            <p className="text-[13px] leading-snug" style={{ color: 'var(--lia-text-secondary)' }}>Modifique situação e envie notificações</p>
          </div>
        </button>
      </div>

      <div className="w-full max-w-3xl mt-auto lg:mt-0">
        <div 
          className="relative flex items-center bg-white rounded-2xl border"
          style={{ 
            borderColor: 'var(--lia-border-default)',
            boxShadow: '0 2px 6px rgba(0,0,0,0.02)'
          }}
        >
          <button className="p-3 ml-1 text-gray-400 hover:text-gray-600 transition-colors">
            <Paperclip size={20} />
          </button>
          <div className="h-6 w-[1px] bg-gray-200 mx-1"></div>
          <button className="p-3 text-gray-400 hover:text-gray-600 transition-colors">
            <Search size={20} />
          </button>
          
          <textarea 
            className="flex-1 py-4 px-2 bg-transparent border-none outline-none resize-none text-[15px]"
            rows={1}
            placeholder="Peça a LIA..."
            style={{ 
              color: 'var(--lia-text-primary)',
              minHeight: '56px',
              maxHeight: '200px'
            }}
          />
          
          <button className="p-3 text-gray-400 hover:text-gray-600 transition-colors">
            <Mic size={20} />
          </button>
          <button 
            className="p-2.5 mr-2 rounded-xl text-white transition-colors"
            style={{ backgroundColor: 'var(--wedo-cyan)' }}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default ElevatedCards;