"use client"

import React from "react"
import Link from "next/link"
import { Building2, Globe, ArrowLeft, Shield, AlertTriangle, CheckCircle2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"

const subprocessors = [
  { id: 1, name: 'Amazon Web Services', service: 'Cloud Infrastructure', country: 'EUA', dataTypes: 'Dados de candidatos, Logs', risk: 'low', lastReview: '2024-12-01' },
  { id: 2, name: 'Anthropic', service: 'AI/LLM', country: 'EUA', dataTypes: 'Textos de análise', risk: 'medium', lastReview: '2024-11-15' },
  { id: 3, name: 'Neon', service: 'Database', country: 'EUA', dataTypes: 'Dados de candidatos', risk: 'low', lastReview: '2024-10-20' },
  { id: 4, name: 'SendGrid', service: 'Email', country: 'EUA', dataTypes: 'Emails de candidatos', risk: 'low', lastReview: '2024-09-10' },
  { id: 5, name: 'Pearch AI', service: 'Candidate Search', country: 'EUA', dataTypes: 'Perfis públicos', risk: 'low', lastReview: '2024-11-01' },
]

function getRiskBadge(risk: string) {
  switch (risk) {
    case 'low':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3.5 h-3.5" />Baixo</Badge>
    case 'medium':
      return <Badge variant="warning" className="gap-1"><AlertTriangle className="w-3.5 h-3.5" />Médio</Badge>
    case 'high':
      return <Badge variant="danger" className="gap-1"><Shield className="w-3.5 h-3.5" />Alto</Badge>
    default:
      return null
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

export default function SubprocessadoresPage() {
  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link 
            href="/admin/compliance/trust-center"
            className="inline-flex items-center gap-1 text-sm hover:underline text-lia-text-primary"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao Trust Center
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-lia-interactive-active/30"
          >
            <Building2 className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
              
            >
              Subprocessadores
            </h1>
            <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
              Lista de subprocessadores e terceiros autorizados
            </p>
          </div>
        </div>
        
        <div 
          className="rounded-md border overflow-hidden bg-lia-bg-primary dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle"
          
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr 
                  className="border-b bg-lia-bg-secondary dark:bg-lia-bg-primary border-lia-border-subtle dark:border-lia-border-subtle"
                  
                >
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Subprocessador
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Tipo de Serviço
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    País/Região
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Dados Processados
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Avaliação de Risco
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Última Revisão
                  </th>
                </tr>
              </thead>
              <tbody>
                {subprocessors.map((sub, index) => (
                  <tr 
                    key={sub.id}
                    className={`border-b hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none border-lia-border-subtle dark:border-lia-border-subtle ${index % 2 !== 0 ? 'bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`}
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {sub.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span 
                        className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-lia-interactive-active/30"
                      >
                        {sub.service}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5 text-lia-text-tertiary dark:text-lia-text-secondary"  />
                        <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                          {sub.country}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                        {sub.dataTypes}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      {getRiskBadge(sub.risk)}
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                        {formatDate(sub.lastReview)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div 
          className="mt-4 p-4 rounded-md border bg-lia-interactive-active/20 border-wedo-cyan/20"
        >
          <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
            <strong>Transparência:</strong> Todos os subprocessadores passam por avaliação de segurança e possuem acordos de processamento de dados (DPA) assinados. Notificamos nossos clientes sobre qualquer alteração nesta lista com antecedência mínima de 30 dias.
          </p>
        </div>
      </div>
    </div>
  )
}
