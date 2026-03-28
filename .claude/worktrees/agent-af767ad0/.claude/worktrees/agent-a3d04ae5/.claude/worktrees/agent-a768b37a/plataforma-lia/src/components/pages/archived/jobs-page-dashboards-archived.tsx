/**
 * ARQUIVO ARQUIVADO - jobs-page-dashboards-archived.tsx
 * 
 * Este arquivo contém código arquivado da página de vagas que foi removido
 * temporariamente para simplificação da interface. O código pode ser recuperado
 * no futuro para reconstrução em outro local.
 * 
 * Data: 15/01/2026
 * Motivo: Simplificação da página Visão Geral de Vagas
 * 
 * Conteúdo:
 * 1. Botão "Ver Dashboard" do card Minhas Vagas
 * 2. Botão "Ver Dashboard" do card Visão Geral da Empresa
 * 3. Card completo "Performance da LIA"
 * 4. Modal "Minhas Vagas Dashboard"
 * 5. Modal "Visão Geral da Empresa Dashboard"
 * 6. Modal "Performance da LIA Dashboard"
 * 
 * Dependências necessárias para reconstrução:
 * - dashboardStats (estado com métricas)
 * - dashboardPeriod / setDashboardPeriod (seletor de período)
 * - activeDashboardModal / setActiveDashboardModal (controle de modais)
 * - cardStyles, textStyles (design tokens)
 * - Lucide icons: Briefcase, Building2, Brain, X, Clock, TrendingUp, Share2, AlertTriangle
 */

import React from "react"

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 1: BOTÃO "VER DASHBOARD" DO CARD MINHAS VAGAS
// ═══════════════════════════════════════════════════════════════════════════
export const MinhasVagasDashboardButton = () => {
  return (
    <button 
      onClick={() => {/* setActiveDashboardModal('minhasVagas') */}}
      className="w-full px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs font-medium transition-colors"
    >
      Ver Dashboard
    </button>
  )
}

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 2: BOTÃO "VER DASHBOARD" DO CARD VISÃO GERAL DA EMPRESA
// ═══════════════════════════════════════════════════════════════════════════
export const VisaoGeralDashboardButton = () => {
  return (
    <button 
      onClick={() => {/* setActiveDashboardModal('visaoGeral') */}}
      className="w-full px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs font-medium transition-colors"
    >
      Ver Dashboard
    </button>
  )
}

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 3: CARD COMPLETO "PERFORMANCE DA LIA"
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Card que mostrava métricas de performance da LIA na página de visão geral
 * 
 * Exibia:
 * - CVs processados
 * - Horas salvas pela automação
 * - Botões Ver Performance e Ver Dashboard
 */
export const PerformanceLiaCard = ({ dashboardStats }: { dashboardStats: any }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-100 dark:border-gray-700 p-5 flex flex-col">
      <div className="flex items-center gap-2 mb-2">
        {/* <Brain className="w-5 h-5 text-wedo-cyan" /> */}
        <h3 className="text-sm font-semibold text-gray-950 dark:text-gray-50">Performance da LIA</h3>
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400 mb-4">
        <span className="font-medium">{((dashboardStats?.noFunil || 0) * 1.5).toLocaleString()} CVs processados</span>
        <span>•</span>
        <span>{Math.round((dashboardStats?.noFunil || 0) * 1.2)}h salvas</span>
      </div>
      <div className="flex flex-col gap-2">
        <button 
          onClick={() => {/* setActiveDashboardModal('performanceLia') */}}
          className="w-full px-3 py-2 rounded-md bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs font-medium transition-colors"
        >
          Ver Performance
        </button>
        <button 
          onClick={() => {/* setActiveDashboardModal('performanceLia') */}}
          className="w-full px-3 py-2 rounded-md border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs font-medium transition-colors"
        >
          Ver Dashboard
        </button>
      </div>
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 4: MODAL "MINHAS VAGAS DASHBOARD"
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Modal de dashboard pessoal do recrutador
 * 
 * Funcionalidades:
 * - Funil visual de candidatos (Candidatos → Triagem → Entrevista → Ofertas → Contratados)
 * - KPIs pessoais (Time to Fill, Taxa de conversão)
 * - Seletor de período (1m, 3m, 6m, 9m, 12m)
 */
export const MinhasVagasDashboardModalCode = `
{/* MODAL: MINHAS VAGAS DASHBOARD */}
{activeDashboardModal === 'minhasVagas' && (
  <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={() => setActiveDashboardModal(null)}>
    <div className={\`\${cardStyles.default} max-w-2xl w-full max-h-[80vh] overflow-y-auto\`} onClick={e => e.stopPropagation()}>
      <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-gray-600" />
          <h3 className="text-base font-semibold text-gray-950 dark:text-gray-50">Minhas Vagas</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {(['1m', '3m', '6m', '9m', '12m'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setDashboardPeriod(period)}
                className={\`px-2 py-1 text-[10px] font-medium rounded-full transition-colors \${
                  dashboardPeriod === period
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }\`}
              >
                {period.toUpperCase()}
              </button>
            ))}
          </div>
          <button onClick={() => setActiveDashboardModal(null)} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>
      <div className="p-5">
        <div className="flex gap-4">
          <div className="w-1/2">
            <div className="text-xs text-gray-500 font-medium mb-3">Meu Funil</div>
            <div className="flex flex-col items-center gap-1">
              {(() => {
                const totalFunil = dashboardStats?.noFunil || 0;
                const triagem = Math.round(totalFunil * 0.65);
                const entrevistas = dashboardStats?.entrevistasRecentes || Math.round(totalFunil * 0.35);
                const ofertas = dashboardStats?.ofertas || Math.round(totalFunil * 0.08);
                const contratados = dashboardStats?.concluidas || Math.round(totalFunil * 0.04);
                const stages = [
                  { label: 'Candidatos', value: totalFunil, width: 100 },
                  { label: 'Triagem', value: triagem, width: 82, color: '#A8D5C2' },
                  { label: 'Entrevista', value: entrevistas, width: 64, color: '#C5E5D8' },
                  { label: 'Ofertas', value: ofertas, width: 46, color: '#D5C9BA' },
                  { label: 'Contratados', value: contratados, width: 28, color: '#5DA47A' },
                ];
                return stages.map((stage, idx) => (
                  <div key={idx} className="flex flex-col items-center w-full">
                    <div 
                      className="h-6 rounded-sm flex items-center justify-center gap-1"
                      style={{ width: \`\${stage.width}%\`, backgroundColor: stage.color }}
                    >
                      <span className="text-xs font-bold text-white">{stage.value}</span>
                      <span className="text-xs text-white/80">{stage.label}</span>
                    </div>
                  </div>
                ));
              })()}
            </div>
          </div>
          <div className="flex-1">
            <div className="text-xs text-gray-500 font-medium mb-3">Meus KPIs</div>
            <div className="grid grid-cols-2 gap-2">
              <div className="text-center p-3 rounded-md bg-gray-900/[0.12]">
                <div className="text-xl font-bold text-gray-700">{dashboardStats?.ttfMedio || 32}d</div>
                <div className="text-xs text-gray-500">Time to Fill</div>
              </div>
              <div className="text-center p-3 rounded-md bg-wedo-green/[0.125]">
                <div className="text-xl font-bold text-wedo-green">{dashboardStats?.taxaConversao || 12}%</div>
                <div className="text-xs text-gray-500">Conversão</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)}
`

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 5: MODAL "VISÃO GERAL DA EMPRESA DASHBOARD"
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Modal de dashboard da empresa
 * 
 * Funcionalidades:
 * - Métricas por departamento
 * - Performance por canal de recrutamento (LinkedIn, Indicações, Site, Job Boards)
 * - Tendências de contratação
 * - Seletor de período (1m, 3m, 6m, 9m, 12m)
 */
export const VisaoGeralDashboardModalCode = `
{/* MODAL: VISÃO GERAL DA EMPRESA DASHBOARD */}
{activeDashboardModal === 'visaoGeral' && (
  <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={() => setActiveDashboardModal(null)}>
    <div className={\`\${cardStyles.default} max-w-3xl w-full max-h-[85vh] overflow-y-auto\`} onClick={e => e.stopPropagation()}>
      <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Building2 className="w-5 h-5 text-gray-600" />
          <h3 className="text-base font-semibold text-gray-950 dark:text-gray-50">Visão Geral da Empresa</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {(['1m', '3m', '6m', '9m', '12m'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setDashboardPeriod(period)}
                className={\`px-2 py-1 text-[10px] font-medium rounded-full transition-colors \${
                  dashboardPeriod === period
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }\`}
              >
                {period.toUpperCase()}
              </button>
            ))}
          </div>
          <button onClick={() => setActiveDashboardModal(null)} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>
      <div className="p-5">
        {/* ... conteúdo do modal ... */}
        <div className="flex gap-4">
          <div className="w-[45%]">
            <div className="text-xs text-gray-500 font-medium mb-3">Por Departamento</div>
            {/* Grid de departamentos com métricas */}
          </div>
          <div className="flex-1">
            <div className="text-xs text-gray-500 font-medium mb-2 flex items-center gap-1">
              <Share2 className="w-2.5 h-2.5" />
              Performance por Canal
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-1">
              {[
                { name: 'LinkedIn Jobs', rate: 14.3 },
                { name: 'Indicações', rate: 22.8, color: '#5DA47A' },
                { name: 'Site Corporativo', rate: 9.7, color: '#E5A853' },
                { name: 'Job Boards', rate: 4.3, color: '#C8A0E5' },
              ].map((channel, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-1">
                    <div className="w-1 h-3 rounded-full" style={{ backgroundColor: channel.color }} />
                    <span className="text-xs text-gray-800 dark:text-gray-200">{channel.name}</span>
                  </div>
                  <span className="text-xs font-bold px-1.5 py-0.5 rounded" style={{ backgroundColor: \`\${channel.color}20\`, color: channel.color }}>
                    {channel.rate}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)}
`

// ═══════════════════════════════════════════════════════════════════════════
// SEÇÃO 6: MODAL "PERFORMANCE DA LIA DASHBOARD"
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Modal de dashboard de performance da IA
 * 
 * Funcionalidades:
 * - Métricas de automação (CVs processados, triagens enviadas)
 * - Funil de automação (Mapeados → CVs → Enviados → Concluídos → Agendamentos)
 * - KPIs de economia (Horas salvas, ROI)
 * - Métricas de IA (Eficiência, Tempo reduzido, Precisão, Contratados, etc.)
 * - Status de automação (ON/24/7)
 */
export const PerformanceLiaDashboardModalCode = `
{/* MODAL: PERFORMANCE DA LIA */}
{activeDashboardModal === 'performanceLia' && (
  <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] z-50 flex items-center justify-center p-4" onClick={() => setActiveDashboardModal(null)}>
    <div className={\`\${cardStyles.default} max-w-3xl w-full max-h-[85vh] overflow-y-auto\`} onClick={e => e.stopPropagation()}>
      <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-wedo-cyan" />
          <h3 className="text-base font-semibold text-gray-950 dark:text-gray-50">Performance da LIA</h3>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            {(['1m', '3m', '6m', '9m', '12m'] as const).map((period) => (
              <button
                key={period}
                onClick={() => setDashboardPeriod(period)}
                className={\`px-2 py-1 text-[10px] font-medium rounded-full transition-colors \${
                  dashboardPeriod === period
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                }\`}
              >
                {period.toUpperCase()}
              </button>
            ))}
          </div>
          <button onClick={() => setActiveDashboardModal(null)} className="p-1 hover:bg-gray-100 rounded-md transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>
      </div>
      <div className="p-5">
        <div className="flex gap-4">
          <div className="w-[40%]">
            <div className="text-xs text-gray-500 font-medium mb-3">Automação LIA</div>
            <div className="grid grid-cols-2 gap-2 mb-3">
              <div className="text-center p-3 rounded-md bg-gray-100 dark:bg-gray-800">
                <div className="text-xl font-bold text-gray-900 dark:text-gray-50">{((dashboardStats?.noFunil || 0) * 1.5).toLocaleString()}</div>
                <div className="text-xs text-gray-500">CVs Processados</div>
              </div>
              <div className="text-center p-3 rounded-md bg-wedo-green/10">
                <div className="text-xl font-bold text-wedo-green">{Math.round((dashboardStats?.noFunil || 0) * 0.7)}</div>
                <div className="text-xs text-gray-500">Triagens Enviadas</div>
              </div>
            </div>
            {/* ... funil de automação e KPIs ... */}
          </div>
          <div className="flex-1">
            <div className="text-xs text-gray-500 font-medium mb-3">Métricas de IA</div>
            <div className="grid grid-cols-3 gap-2">
              <div className="text-center p-2 rounded-md bg-wedo-green/15">
                <div className="text-sm font-bold text-wedo-green">{Math.round(((dashboardStats?.noFunil || 0) / Math.max(dashboardStats?.ativas || 1, 1)) * 10)}x</div>
                <div className="text-xs text-gray-500">Eficiência</div>
              </div>
              <div className="text-center p-2 rounded-md bg-[#A8D5C2]/20">
                <div className="text-sm font-bold text-wedo-green">-{Math.min(dashboardStats?.ttfMedio || 0, 50)}%</div>
                <div className="text-xs text-gray-500">Tempo Reduzido</div>
              </div>
              <div className="text-center p-2 rounded-md bg-gray-100 dark:bg-gray-800">
                <div className="text-sm font-bold text-gray-900 dark:text-gray-50">92%</div>
                <div className="text-xs text-gray-500">Precisão</div>
              </div>
              {/* ... mais métricas ... */}
            </div>
          </div>
        </div>
        <div className="mt-4 pt-3 border-t border-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 p-2 rounded-md bg-gray-100">
                <AlertTriangle className="w-3 h-3 text-gray-400" />
                <span className="text-xs text-gray-800 dark:text-gray-200">
                  {dashboardStats?.pipelineVazio > 0 
                    ? <span className="font-medium">{dashboardStats.pipelineVazio} vagas precisam de candidatos</span>
                    : <span className="font-medium">Todos os indicadores normais</span>}
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <div className="text-center px-3 py-1.5 rounded-md bg-wedo-green/10">
                <div className="text-xs font-bold text-wedo-green">ON</div>
                <div className="text-xs text-gray-500">Auto</div>
              </div>
              <div className="text-center px-3 py-1.5 rounded-md bg-gray-100 dark:bg-gray-800">
                <div className="text-xs font-bold text-gray-900 dark:text-gray-50">24/7</div>
                <div className="text-xs text-gray-500">Ativo</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
)}
`

// ═══════════════════════════════════════════════════════════════════════════
// INSTRUÇÕES DE RECUPERAÇÃO
// ═══════════════════════════════════════════════════════════════════════════
/**
 * Para recuperar este código:
 * 
 * 1. Copie os componentes/código desejados deste arquivo
 * 2. Adicione os imports necessários no arquivo de destino:
 *    - import { Briefcase, Building2, Brain, X, Clock, TrendingUp, Share2, AlertTriangle } from "lucide-react"
 *    - import { cardStyles, textStyles } from '@/lib/design-tokens'
 * 
 * 3. Adicione o estado necessário:
 *    - const [activeDashboardModal, setActiveDashboardModal] = useState<string | null>(null)
 *    - const [dashboardPeriod, setDashboardPeriod] = useState<'1m' | '3m' | '6m' | '9m' | '12m'>('3m')
 *    - dashboardStats (objeto com métricas do dashboard)
 * 
 * 4. Cole o código JSX no local apropriado
 */
