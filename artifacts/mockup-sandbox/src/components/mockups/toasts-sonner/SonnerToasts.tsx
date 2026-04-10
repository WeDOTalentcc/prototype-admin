import React from 'react';
import './_group.css';

type ToastType = 'success' | 'error' | 'info' | 'warning' | 'loading' | 'default';

interface ToastItem {
  type: ToastType;
  title: string;
  description?: string;
  label: string;
}

const SONNER_COLORS: Record<ToastType, { bg: string; border: string; icon: string; iconBg: string; titleColor: string }> = {
  success: {
    bg: 'var(--toast-success-light)',
    border: 'var(--toast-success-border)',
    icon: '#16a34a',
    iconBg: 'rgba(22,163,74,0.15)',
    titleColor: '#15803d',
  },
  error: {
    bg: 'var(--toast-error-light)',
    border: 'var(--toast-error-border)',
    icon: '#DC2626',
    iconBg: 'rgba(220,38,38,0.12)',
    titleColor: '#b91c1c',
  },
  info: {
    bg: 'var(--toast-info-light)',
    border: 'var(--toast-info-border)',
    icon: '#2563eb',
    iconBg: 'rgba(37,99,235,0.12)',
    titleColor: '#1d4ed8',
  },
  warning: {
    bg: 'var(--toast-warning-light)',
    border: 'var(--toast-warning-border)',
    icon: '#d97706',
    iconBg: 'rgba(217,119,6,0.12)',
    titleColor: '#b45309',
  },
  loading: {
    bg: '#F9FAFB',
    border: 'var(--lia-border-default)',
    icon: 'var(--lia-text-secondary)',
    iconBg: 'var(--lia-interactive-active)',
    titleColor: 'var(--lia-text-primary)',
  },
  default: {
    bg: '#FFFFFF',
    border: 'var(--lia-border-default)',
    icon: 'var(--lia-text-primary)',
    iconBg: 'var(--lia-bg-tertiary)',
    titleColor: 'var(--lia-text-primary)',
  },
};

function SuccessIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="9 12 11 14 15 10" />
    </svg>
  );
}

function ErrorIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="12" />
      <line x1="12" y1="16" x2="12.01" y2="16" />
    </svg>
  );
}

function InfoIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="16" x2="12" y2="12" />
      <line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  );
}

function WarningIcon({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function LoadingSpinner({ color }: { color: string }) {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        .spin-icon { animation: spin 1s linear infinite; transform-origin: center; }
      `}</style>
      <g className="spin-icon">
        <path d="M21 12a9 9 0 1 1-6.219-8.56" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      </g>
    </svg>
  );
}

function XIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function getIcon(type: ToastType, color: string) {
  switch (type) {
    case 'success': return <SuccessIcon color={color} />;
    case 'error': return <ErrorIcon color={color} />;
    case 'info': return <InfoIcon color={color} />;
    case 'warning': return <WarningIcon color={color} />;
    case 'loading': return <LoadingSpinner color={color} />;
    default: return null;
  }
}

function SonnerToastCard({ toast }: { toast: ToastItem }) {
  const colors = SONNER_COLORS[toast.type];

  return (
    <div
      style={{
        background: toast.type === 'loading' || toast.type === 'default' ? '#FFFFFF' : colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: '10px',
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        width: '356px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.05)',
        position: 'relative',
        fontFamily: "'Open Sans', sans-serif",
      }}
    >
      <div
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: colors.iconBg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: toast.description ? '1px' : '0',
        }}
      >
        {getIcon(toast.type, colors.icon)}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{
          margin: 0,
          fontSize: '13.5px',
          fontWeight: '600',
          color: toast.type === 'loading' ? 'var(--lia-text-primary)' : colors.titleColor,
          lineHeight: '1.4',
          fontFamily: "'Open Sans', sans-serif",
        }}>
          {toast.title}
        </p>
        {toast.description && (
          <p style={{
            margin: '3px 0 0',
            fontSize: '12.5px',
            color: 'var(--lia-text-secondary)',
            lineHeight: '1.45',
            fontFamily: "'Open Sans', sans-serif",
          }}>
            {toast.description}
          </p>
        )}
      </div>

      <button style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '2px',
        color: 'var(--lia-text-tertiary)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '4px',
        flexShrink: 0,
        marginTop: '2px',
      }}>
        <XIcon />
      </button>
    </div>
  );
}

function ToastSlot({ toast }: { toast: ToastItem }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-start' }}>
      <span style={{
        fontSize: '10px',
        fontWeight: '600',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: 'var(--lia-text-tertiary)',
        fontFamily: "'Inter', sans-serif",
        paddingLeft: '2px',
      }}>
        {toast.label}
      </span>
      <SonnerToastCard toast={toast} />
    </div>
  );
}

const TOASTS: ToastItem[] = [
  {
    type: 'success',
    label: 'Success — com descrição',
    title: 'Arquétipo salvo!',
    description: 'As configurações foram salvas com sucesso.',
  },
  {
    type: 'success',
    label: 'Success simples — só título',
    title: 'Link copiado!',
  },
  {
    type: 'error',
    label: 'Error — com descrição',
    title: 'Erro ao salvar',
    description: 'Não foi possível salvar as configurações. Tente novamente.',
  },
  {
    type: 'error',
    label: 'Error simples — só título',
    title: 'Erro ao desbloquear pipeline',
  },
  {
    type: 'info',
    label: 'Info — com descrição',
    title: 'Arquivo recebido',
    description: 'Transcrição concluída e disponível para revisão.',
  },
  {
    type: 'warning',
    label: 'Warning — com descrição',
    title: 'Aviso',
    description: 'Comunicações não foram transferidas para o novo estágio.',
  },
  {
    type: 'loading',
    label: 'Loading — com spinner',
    title: 'Processando exportação...',
  },
];

const DARK_TOASTS: ToastItem[] = [
  {
    type: 'success',
    label: 'Success — com descrição',
    title: 'Exportação concluída',
    description: 'O relatório foi gerado e está pronto para download.',
  },
  {
    type: 'success',
    label: 'Success simples — só título',
    title: 'Candidato aprovado!',
  },
  {
    type: 'error',
    label: 'Error — com descrição',
    title: 'Erro de conexão',
    description: 'Não foi possível conectar ao servidor. Verifique sua rede.',
  },
  {
    type: 'error',
    label: 'Error simples — só título',
    title: 'Erro ao excluir registro',
  },
  {
    type: 'info',
    label: 'Info — com descrição',
    title: 'Nova vaga disponível',
    description: 'Uma nova vaga compatível com seu perfil foi adicionada.',
  },
  {
    type: 'warning',
    label: 'Warning — com descrição',
    title: 'Sessão expirando',
    description: 'Sua sessão expira em 5 minutos. Salve seu trabalho.',
  },
  {
    type: 'loading',
    label: 'Loading — com spinner',
    title: 'Analisando candidatos...',
  },
];

const DARK_BG = '#111827';
const DARK_CARD_BG = '#1F2937';
const DARK_BORDER = 'rgba(255,255,255,0.10)';

function DarkSonnerToastCard({ toast }: { toast: ToastItem }) {
  const colors = SONNER_COLORS[toast.type];

  const darkIconBg: Record<ToastType, string> = {
    success: 'rgba(22,163,74,0.20)',
    error: 'rgba(220,38,38,0.20)',
    info: 'rgba(37,99,235,0.20)',
    warning: 'rgba(217,119,6,0.20)',
    loading: 'rgba(255,255,255,0.10)',
    default: 'rgba(255,255,255,0.08)',
  };

  const darkBorderColor: Record<ToastType, string> = {
    success: 'rgba(22,163,74,0.30)',
    error: 'rgba(220,38,38,0.30)',
    info: 'rgba(37,99,235,0.30)',
    warning: 'rgba(217,119,6,0.30)',
    loading: DARK_BORDER,
    default: DARK_BORDER,
  };

  const darkTitleColor: Record<ToastType, string> = {
    success: '#4ade80',
    error: '#f87171',
    info: '#93c5fd',
    warning: '#fbbf24',
    loading: '#F9FAFB',
    default: '#F9FAFB',
  };

  return (
    <div
      style={{
        background: DARK_CARD_BG,
        border: `1px solid ${darkBorderColor[toast.type]}`,
        borderRadius: '10px',
        padding: '14px 16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        width: '356px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.35)',
        position: 'relative',
        fontFamily: "'Open Sans', sans-serif",
      }}
    >
      <div
        style={{
          width: '28px',
          height: '28px',
          borderRadius: '50%',
          background: darkIconBg[toast.type],
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: toast.description ? '1px' : '0',
        }}
      >
        {getIcon(toast.type, colors.icon)}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{
          margin: 0,
          fontSize: '13.5px',
          fontWeight: '600',
          color: darkTitleColor[toast.type],
          lineHeight: '1.4',
          fontFamily: "'Open Sans', sans-serif",
        }}>
          {toast.title}
        </p>
        {toast.description && (
          <p style={{
            margin: '3px 0 0',
            fontSize: '12.5px',
            color: '#9CA3AF',
            lineHeight: '1.45',
            fontFamily: "'Open Sans', sans-serif",
          }}>
            {toast.description}
          </p>
        )}
      </div>

      <button style={{
        background: 'none',
        border: 'none',
        cursor: 'pointer',
        padding: '2px',
        color: '#6B7280',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        borderRadius: '4px',
        flexShrink: 0,
        marginTop: '2px',
      }}>
        <XIcon />
      </button>
    </div>
  );
}

function DarkToastSlot({ toast }: { toast: ToastItem }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'flex-start' }}>
      <span style={{
        fontSize: '10px',
        fontWeight: '600',
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        color: '#6B7280',
        fontFamily: "'Inter', sans-serif",
        paddingLeft: '2px',
      }}>
        {toast.label}
      </span>
      <DarkSonnerToastCard toast={toast} />
    </div>
  );
}

export default function SonnerToasts() {
  return (
    <div style={{ fontFamily: "'Open Sans', sans-serif", minHeight: '100vh', background: '#F3F4F6', padding: '48px 32px' }}>
      <div style={{ maxWidth: '1280px', margin: '0 auto' }}>

        <div style={{ marginBottom: '48px' }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: '700',
            color: '#111827',
            fontFamily: "'Open Sans', sans-serif",
            margin: '0 0 8px',
          }}>
            Toasts Sonner — Plataforma LIA
          </h1>
          <p style={{
            fontSize: '14px',
            color: '#6B7280',
            margin: 0,
            fontFamily: "'Open Sans', sans-serif",
          }}>
            Todos os tipos de toast com <code style={{ background: '#E5E7EB', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontFamily: "'JetBrains Mono', monospace" }}>richColors</code> — posição <code style={{ background: '#E5E7EB', padding: '2px 6px', borderRadius: '4px', fontSize: '12px', fontFamily: "'JetBrains Mono', monospace" }}>top-right</code>
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', alignItems: 'start' }}>

          <div style={{
            background: '#FFFFFF',
            borderRadius: '16px',
            padding: '32px',
            border: '1px solid #E5E7EB',
            boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '28px',
              paddingBottom: '16px',
              borderBottom: '1px solid #F3F4F6',
            }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#E5E7EB' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#E5E7EB' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#E5E7EB' }} />
              <span style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#6B7280',
                marginLeft: '6px',
                fontFamily: "'Inter', sans-serif",
                letterSpacing: '0.04em',
              }}>
                LIGHT MODE
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {TOASTS.map((t, i) => (
                <ToastSlot key={i} toast={t} />
              ))}
            </div>
          </div>

          <div style={{
            background: DARK_BG,
            borderRadius: '16px',
            padding: '32px',
            border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 4px 24px rgba(0,0,0,0.3)',
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              marginBottom: '28px',
              paddingBottom: '16px',
              borderBottom: '1px solid rgba(255,255,255,0.08)',
            }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'rgba(255,255,255,0.15)' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'rgba(255,255,255,0.15)' }} />
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: 'rgba(255,255,255,0.15)' }} />
              <span style={{
                fontSize: '12px',
                fontWeight: '600',
                color: '#6B7280',
                marginLeft: '6px',
                fontFamily: "'Inter', sans-serif",
                letterSpacing: '0.04em',
              }}>
                DARK MODE
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {DARK_TOASTS.map((t, i) => (
                <DarkToastSlot key={i} toast={t} />
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
