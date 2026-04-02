"use client"

import React from "react"
import Link from "next/link"
import { ChevronRight } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  scope?: 'global' | 'client'
  clientName?: string
  className?: string
}

export function Breadcrumbs({ 
  items, 
  scope, 
  clientName,
  className 
}: BreadcrumbsProps) {
  return (
    <nav 
      className={cn("flex items-center gap-2 text-sm", className)}
      aria-label="Breadcrumb"
    >
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        
        return (
          <React.Fragment key={item.label || index}>
            {index > 0 && (
              <ChevronRight
                className="w-4 h-4 shrink-0 text-lia-text-disabled"
              />
            )}

            {item.href && !isLast ? (
              <Link
                href={item.href}
                className="hover:text-lia-text-primary dark:hover:text-lia-text-inverse transition-colors motion-reduce:transition-none shrink-0 text-lia-text-disabled"
              >
                {item.label}
              </Link>
            ) : (
              <span
                className={`shrink-0 ${isLast ? 'text-lia-text-primary' : 'text-lia-text-disabled'}`}
              >
                {item.label}
              </span>
            )}
            
            {isLast && scope && (
              <Badge 
                variant="outline" 
                className="text-micro font-medium ml-1"
                style={
                  scope === 'global' 
                    ? { borderColor: 'var(--lia-border-subtle)' }
                    : { borderColor: 'var(--wedo-purple)', color: 'var(--wedo-purple)' }
                }
              >
                {scope === 'global' ? 'GLOBAL' : `Cliente: ${clientName || 'N/A'}`}
              </Badge>
            )}
          </React.Fragment>
        )
      })}
    </nav>
  )
}

export function generateBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split('/').filter(Boolean)
  const breadcrumbs: BreadcrumbItem[] = []
  
  const labelMap: Record<string, string> = {
    'admin': 'Admin',
    'clientes': 'Clientes',
    'compliance': 'Compliance & Segurança',
    'trust-center': 'Trust Center',
    'controles': 'Controles',
    'lgpd': 'LGPD & Privacidade',
    'riscos': 'Gestão de Riscos',
    'monitoramento': 'Monitoramento',
    'auditoria': 'Sala de Auditoria',
    'configuracoes': 'Configurações',
    'certificacoes': 'Certificações',
    'subprocessadores': 'Subprocessadores',
    'recursos': 'Recursos',
    'iso-27001': 'ISO 27001',
    'soc-2': 'SOC 2',
    'sox': 'SOX',
    'cobertura': 'Cobertura',
    'dpo': 'DPO',
    'portal-titular': 'Portal do Titular',
    'consentimentos': 'Consentimentos',
    'transferencias': 'Transferências',
    'registro': 'Risk Register',
    'continuidade': 'Continuidade',
    'fornecedores': 'Fornecedores',
    'seguro': 'Seguro Cibernético',
    'dashboard-seguranca': 'Dashboard Segurança',
    'incidentes': 'Incidentes',
    'soc-siem': 'SOC/SIEM',
    'alertas': 'Alertas',
    'logs': 'Logs',
    'bias': 'Auditorias de Bias',
    'sod': 'Matriz SoD',
    'treinamentos': 'Treinamentos',
    'exportar': 'Exportar Pacote',
    'templates': 'Templates',
    'politicas': 'Políticas',
    'comunicacoes': 'Comunicações',
    'metricas-plataforma': 'Métricas da Plataforma',
    'setup-empresa': 'Setup de Empresa',
    'usuarios': 'Usuários',
    'setup': 'Setup',
    'faturamento': 'Faturamento',
    'metricas': 'Métricas',
    'integracoes': 'Integrações',
    'automacoes': 'Automações',
    'big-five': 'Big Five',
    'testes': 'Testes',
    'workforce': 'Workforce',
    'jornada': 'Jornada',
    'consumo-ia': 'Consumo de IA',
    'observabilidade': 'Observabilidade',
  }
  
  let currentPath = ''
  
  for (let i = 0; i < segments.length; i++) {
    const segment = segments[i]
    currentPath += `/${segment}`
    
    if (segment.match(/^[0-9a-f-]{36}$/i) || segment === '[clientId]') {
      continue
    }
    
    const label = labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' ')
    
    breadcrumbs.push({
      label,
      href: i < segments.length - 1 ? currentPath : undefined
    })
  }
  
  return breadcrumbs
}
