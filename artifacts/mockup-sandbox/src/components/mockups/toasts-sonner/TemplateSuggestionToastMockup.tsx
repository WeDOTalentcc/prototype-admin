import React from 'react';
import './_group.css';

function XIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function ZapIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

function BrainIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.96-3.41 3 3 0 0 1 .34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.76-3.31z"/>
      <path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.96-3.41 3 3 0 0 0-.34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.76-3.31z"/>
    </svg>
  );
}

function LightbulbIcon({ color }: { color: string }) {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="9" y1="18" x2="15" y2="18" />
      <line x1="10" y1="22" x2="14" y2="22" />
      <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

function FileTextIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function ArchiveIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
      <polyline points="21 8 21 21 3 21 3 8" />
      <rect x="1" y="3" width="22" height="5" />
      <line x1="10" y1="12" x2="14" y2="12" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

interface TemplateCardProps {
  variant: 'repetitions' | 'complexity' | 'default';
  dark?: boolean;
}

function getVariantData(variant: 'repetitions' | 'complexity' | 'default') {
  switch (variant) {
    case 'repetitions':
      return {
        icon: <ZapIcon color="#D19960" />,
        badgeText: 'Ação frequente · 5 repetições',
        badgeStyle: {
          background: 'rgba(209,153,96,0.12)',
          color: '#D19960',
          border: '1px solid rgba(209,153,96,0.30)',
        },
        command: 'Triagem completa do candidato João Silva com análise de fit cultural e técnico',
        estimatedTime: 8,
        complexity: 6,
        label: 'Variação: Repetições (≥ 3x)',
      };
    case 'complexity':
      return {
        icon: <BrainIcon color="#9860D1" />,
        badgeText: 'Alta complexidade · 9/10',
        badgeStyle: {
          background: 'rgba(152,96,209,0.12)',
          color: '#9860D1',
          border: '1px solid rgba(152,96,209,0.25)',
        },
        command: 'Pipeline completo: triagem → entrevista técnica → avaliação cultural → oferta → onboarding',
        estimatedTime: 18,
        complexity: 9,
        label: 'Variação: Complexidade alta (≥ 8)',
      };
    case 'default':
    default:
      return {
        icon: <LightbulbIcon color="#6B7280" />,
        badgeText: 'Sugestão inteligente da LIA',
        badgeStyle: {
          background: '#F3F4F6',
          color: '#6B7280',
          border: '1px solid #E5E7EB',
        },
        command: 'Enviar boas-vindas ao novo candidato com kit de integração personalizado',
        estimatedTime: 4,
        complexity: 4,
        label: 'Variação: Padrão / Sugestão geral',
      };
  }
}

function TemplateToastCard({ variant, dark = false }: TemplateCardProps) {
  const data = getVariantData(variant);

  const bg = dark ? '#1F2937' : '#FFFFFF';
  const borderColor = dark ? 'rgba(255,255,255,0.10)' : '#D1D5DB';
  const titleColor = dark ? '#F9FAFB' : '#111827';
  const commandBg = dark ? '#111827' : '#F9FAFB';
  const commandColor = dark ? '#D1D5DB' : '#374151';
  const benefitColor = dark ? '#9CA3AF' : '#6B7280';
  const footerBorderColor = dark ? 'rgba(255,255,255,0.08)' : '#E5E7EB';
  const footerTextColor = dark ? '#9CA3AF' : '#6B7280';
  const dismissColor = dark ? 'rgba(255,255,255,0.08)' : '#F3F4F6';
  const dismissTextColor = dark ? '#D1D5DB' : '#374151';
  const notAskColor = dark ? 'transparent' : 'transparent';
  const notAskTextColor = dark ? '#9CA3AF' : '#6B7280';
  const btnBg = dark ? '#F9FAFB' : '#111827';
  const btnText = dark ? '#111827' : '#FFFFFF';
  const xColor = dark ? '#6B7280' : '#9CA3AF';

  const badgeStyleDark: Record<'repetitions' | 'complexity' | 'default', React.CSSProperties> = {
    repetitions: { background: 'rgba(209,153,96,0.18)', color: '#FBBF24', border: '1px solid rgba(209,153,96,0.35)' },
    complexity: { background: 'rgba(152,96,209,0.18)', color: '#C084FC', border: '1px solid rgba(152,96,209,0.35)' },
    default: { background: 'rgba(255,255,255,0.06)', color: '#9CA3AF', border: '1px solid rgba(255,255,255,0.10)' },
  };

  const badgeStyle = dark ? badgeStyleDark[variant] : data.badgeStyle;

  return (
    <div style={{
      background: bg,
      border: `1px solid ${borderColor}`,
      borderLeft: `4px solid ${dark ? '#4DA8BB' : '#60BED1'}`,
      borderRadius: '10px',
      width: '320px',
      boxShadow: dark ? '0 4px 20px rgba(0,0,0,0.40)' : '0 4px 12px rgba(0,0,0,0.08)',
      overflow: 'hidden',
      fontFamily: "'Open Sans', sans-serif",
    }}>
      <div style={{ padding: '14px 14px 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
            {data.icon}
            <span style={{
              fontSize: '12.5px',
              fontWeight: '600',
              color: titleColor,
              fontFamily: "'Open Sans', sans-serif",
            }}>
              Sugestão de Template
            </span>
          </div>
          <button style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            color: xColor,
            display: 'flex',
            alignItems: 'center',
          }}>
            <XIcon />
          </button>
        </div>

        <div style={{ marginBottom: '10px' }}>
          <span style={{
            display: 'inline-block',
            fontSize: '11px',
            fontWeight: '600',
            padding: '3px 8px',
            borderRadius: '20px',
            ...badgeStyle,
            fontFamily: "'Open Sans', sans-serif",
          }}>
            {data.badgeText}
          </span>
        </div>

        <div style={{
          background: commandBg,
          border: `1px solid ${dark ? 'rgba(255,255,255,0.07)' : '#E5E7EB'}`,
          borderRadius: '6px',
          padding: '8px 10px',
          marginBottom: '10px',
        }}>
          <p style={{
            margin: 0,
            fontSize: '11.5px',
            fontFamily: "'JetBrains Mono', monospace",
            color: commandColor,
            lineHeight: '1.5',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical' as const,
            overflow: 'hidden',
          }}>
            "{data.command}"
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: benefitColor, fontSize: '11px' }}>
            <ClockIcon />
            <span>~{data.estimatedTime}min economia</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: benefitColor, fontSize: '11px' }}>
            <FileTextIcon />
            <span>Complexidade {data.complexity}/10</span>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginBottom: '12px' }}>
          <button style={{
            width: '100%',
            background: btnBg,
            color: btnText,
            border: 'none',
            borderRadius: '6px',
            padding: '7px 12px',
            fontSize: '12px',
            fontWeight: '600',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            fontFamily: "'Open Sans', sans-serif",
          }}>
            <ArchiveIcon />
            Criar Template
          </button>

          <div style={{ display: 'flex', gap: '6px' }}>
            <button style={{
              flex: 1,
              background: dismissColor,
              color: dismissTextColor,
              border: `1px solid ${dark ? 'rgba(255,255,255,0.10)' : '#E5E7EB'}`,
              borderRadius: '6px',
              padding: '5px 8px',
              fontSize: '11px',
              fontWeight: '500',
              cursor: 'pointer',
              fontFamily: "'Open Sans', sans-serif",
            }}>
              Agora Não
            </button>
            <button style={{
              flex: 1,
              background: notAskColor,
              color: notAskTextColor,
              border: 'none',
              borderRadius: '6px',
              padding: '5px 8px',
              fontSize: '11px',
              fontWeight: '500',
              cursor: 'pointer',
              fontFamily: "'Open Sans', sans-serif",
            }}>
              Não Perguntar
            </button>
          </div>
        </div>
      </div>

      <div style={{
        borderTop: `1px solid ${footerBorderColor}`,
        padding: '8px 14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <span style={{ fontSize: '11px', color: footerTextColor }}>💡 LIA Intelligence</span>
        <button style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: footerTextColor,
          display: 'flex',
        }}>
          <SettingsIcon />
        </button>
      </div>

      <div style={{
        height: '3px',
        background: dark ? 'rgba(255,255,255,0.05)' : '#F3F4F6',
        position: 'relative',
      }}>
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          height: '100%',
          width: '35%',
          background: dark ? '#4DA8BB' : '#60BED1',
          borderRadius: '0 0 0 0',
          transition: 'width 15s linear',
        }} />
      </div>
    </div>
  );
}

export default function TemplateSuggestionToastMockup() {
  const variants: Array<'repetitions' | 'complexity' | 'default'> = ['repetitions', 'complexity', 'default'];

  return (
    <div style={{ fontFamily: "'Open Sans', sans-serif", minHeight: '100vh', background: '#F3F4F6', padding: '48px 32px' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

        <div style={{ marginBottom: '48px' }}>
          <h1 style={{
            fontSize: '28px',
            fontWeight: '700',
            color: '#111827',
            fontFamily: "'Open Sans', sans-serif",
            margin: '0 0 8px',
          }}>
            TemplateSuggestionToast — 3 Variações
          </h1>
          <p style={{
            fontSize: '14px',
            color: '#6B7280',
            margin: 0,
            fontFamily: "'Open Sans', sans-serif",
          }}>
            Toast customizado com card rico, ícone dinâmico, badge, comando, benefícios e ações — light e dark mode
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>

          <div>
            <h2 style={{
              fontSize: '14px',
              fontWeight: '700',
              color: '#374151',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              fontFamily: "'Inter', sans-serif",
              marginBottom: '24px',
            }}>
              Light Mode
            </h2>
            <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
              {variants.map((v) => (
                <div key={v} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  <span style={{
                    fontSize: '10px',
                    fontWeight: '600',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: '#9CA3AF',
                    fontFamily: "'Inter', sans-serif",
                  }}>
                    {getVariantData(v).label}
                  </span>
                  <TemplateToastCard variant={v} dark={false} />
                </div>
              ))}
            </div>
          </div>

          <div>
            <h2 style={{
              fontSize: '14px',
              fontWeight: '700',
              color: '#6B7280',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              fontFamily: "'Inter', sans-serif",
              marginBottom: '24px',
            }}>
              Dark Mode
            </h2>
            <div style={{
              background: '#111827',
              borderRadius: '16px',
              padding: '32px',
              border: '1px solid rgba(255,255,255,0.06)',
            }}>
              <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap' }}>
                {variants.map((v) => (
                  <div key={v} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <span style={{
                      fontSize: '10px',
                      fontWeight: '600',
                      letterSpacing: '0.08em',
                      textTransform: 'uppercase',
                      color: '#6B7280',
                      fontFamily: "'Inter', sans-serif",
                    }}>
                      {getVariantData(v).label}
                    </span>
                    <TemplateToastCard variant={v} dark={true} />
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
