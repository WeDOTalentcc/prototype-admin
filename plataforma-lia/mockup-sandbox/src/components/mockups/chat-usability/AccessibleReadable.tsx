import React from 'react';
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
import './_group.css';

export function AccessibleReadable() {
  return (
    <div 
      className="flex flex-col min-h-screen bg-[var(--lia-bg-secondary)]" 
      style={{ fontFamily: "'Open Sans', sans-serif" }}
    >
      {/* Main Content Area */}
      <main className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-4 md:p-8">
        
        {/* Welcome Header */}
        <div className="flex flex-col items-center justify-center mt-12 mb-10 text-center">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center shadow-sm border border-[var(--lia-border-subtle)]">
              <Brain className="w-8 h-8 text-[var(--wedo-cyan)]" />
            </div>
            <h1 className="text-2xl md:text-3xl font-semibold text-[var(--lia-text-primary)] tracking-tight flex items-baseline gap-2">
              Oi, eu sou a
              <span 
                className="text-3xl md:text-4xl font-bold text-[var(--wedo-cyan)] tracking-normal"
                style={{ fontFamily: "'Source Serif 4', serif" }}
              >
                LIA.
              </span>
            </h1>
          </div>
          <p className="text-base text-[var(--lia-text-secondary)] font-medium leading-relaxed max-w-lg">
            Como posso ajudar você hoje?
          </p>
        </div>

        {/* Suggestion Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6 mb-12">
          {/* Card 1 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <Plus className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Crie uma nova vaga
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Configure requisitos com descrição detalhada
              </p>
            </div>
          </button>

          {/* Card 2 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <Search className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Buscar candidatos
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Encontre candidatos por perfil, skills ou experiência
              </p>
            </div>
          </button>

          {/* Card 3 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <Search className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Consulte sobre candidato
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Obtenha histórico específico e completo
              </p>
            </div>
          </button>

          {/* Card 4 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <UserCheck className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Adicione novo candidato
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Cadastre perfil com talentos
              </p>
            </div>
          </button>

          {/* Card 5 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <Calendar className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Reagende uma entrevista
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Cancele horário e notifique participantes
              </p>
            </div>
          </button>

          {/* Card 6 */}
          <button className="flex items-start gap-4 p-5 bg-white rounded-xl border border-[var(--lia-border-default)] shadow-sm hover:border-[var(--wedo-cyan)] hover:bg-[var(--lia-bg-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] focus:ring-offset-2 transition-all text-left min-h-[48px]">
            <div className="flex-shrink-0 mt-1 w-10 h-10 bg-[var(--wedo-cyan-light)] bg-opacity-30 rounded-lg flex items-center justify-center">
              <RefreshCcw className="w-6 h-6 text-[var(--wedo-cyan-dark)]" />
            </div>
            <div className="flex flex-col gap-1">
              <h3 className="text-base font-semibold text-[var(--lia-text-primary)] leading-snug">
                Atualize status do candidato
              </h3>
              <p className="text-sm text-[var(--lia-text-secondary)] leading-relaxed">
                Modifique situação e envie notificações
              </p>
            </div>
          </button>
        </div>

        {/* Input Area */}
        <div className="mt-auto pb-4 relative z-10">
          <div className="bg-white rounded-2xl border border-[var(--lia-border-default)] shadow-md focus-within:ring-2 focus-within:ring-[var(--wedo-cyan)] focus-within:border-[var(--wedo-cyan)] transition-all overflow-hidden flex flex-col">
            <textarea 
              className="w-full p-5 bg-transparent border-none resize-none focus:outline-none min-h-[120px] text-base text-[var(--lia-text-primary)] placeholder:text-[var(--lia-text-secondary)] leading-relaxed"
              placeholder="Peça a LIA..."
              aria-label="Mensagem para LIA"
            ></textarea>
            
            <div className="flex items-center justify-between p-3 bg-[var(--lia-bg-secondary)] border-t border-[var(--lia-border-subtle)]">
              <div className="flex items-center gap-2">
                <button 
                  className="w-11 h-11 flex items-center justify-center rounded-lg text-[var(--lia-text-secondary)] hover:bg-[var(--lia-border-subtle)] hover:text-[var(--lia-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] transition-colors"
                  aria-label="Buscar"
                  title="Buscar"
                >
                  <Search className="w-5 h-5" />
                </button>
                <button 
                  className="w-11 h-11 flex items-center justify-center rounded-lg text-[var(--lia-text-secondary)] hover:bg-[var(--lia-border-subtle)] hover:text-[var(--lia-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] transition-colors"
                  aria-label="Anexar arquivo"
                  title="Anexar arquivo"
                >
                  <Paperclip className="w-5 h-5" />
                </button>
              </div>
              
              <div className="flex items-center gap-3">
                <button 
                  className="w-11 h-11 flex items-center justify-center rounded-lg text-[var(--lia-text-secondary)] hover:bg-[var(--lia-border-subtle)] hover:text-[var(--lia-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--wedo-cyan)] transition-colors"
                  aria-label="Mensagem de voz"
                  title="Mensagem de voz"
                >
                  <Mic className="w-5 h-5" />
                </button>
                <button 
                  className="w-12 h-12 flex items-center justify-center rounded-xl bg-[var(--wedo-cyan)] text-white hover:bg-[var(--wedo-cyan-dark)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--wedo-cyan)] shadow-sm transition-all"
                  aria-label="Enviar mensagem"
                  title="Enviar mensagem"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
          
          {/* Explicit Tradeoff Note - Optional but matching the brief intention */}
          <div className="text-center mt-6">
            <p className="text-[13px] text-[var(--lia-text-secondary)] max-w-2xl mx-auto leading-relaxed">
              Design priorizando acessibilidade e legibilidade: Textos e ícones maiores, áreas de clique ampliadas (mínimo 44x44px), maior contraste de cores (WCAG AA) e navegação por teclado visível.
            </p>
          </div>
        </div>

      </main>
    </div>
  );
}
