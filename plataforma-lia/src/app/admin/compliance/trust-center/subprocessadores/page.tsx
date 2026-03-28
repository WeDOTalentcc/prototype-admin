"use client"

import React from "react"
import Link from "next/link"
import { Building2, Globe, ArrowLeft, Shield, AlertTriangle, CheckCircle2 } from "lucide-react"

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
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-status-success/15 text-status-success">
          <CheckCircle2 className="w-3.5 h-3.5" />
          Baixo
        </span>
      )
    case 'medium':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-status-warning/15 text-status-warning">
          <AlertTriangle className="w-3.5 h-3.5" />
          Médio
        </span>
      )
    case 'high':
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-status-error/15 text-status-error">
          <Shield className="w-3.5 h-3.5" />
          Alto
        </span>
      )
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
            className="inline-flex items-center gap-1 text-sm hover:underline text-gray-700"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao Trust Center
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
          >
            <Building2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold text-gray-800 dark:text-gray-100"
              
            >
              Subprocessadores
            </h1>
            <p className="text-sm text-gray-400 dark:text-gray-500" >
              Lista de subprocessadores e terceiros autorizados
            </p>
          </div>
        </div>
        
        <div 
          className="rounded-md border overflow-hidden bg-white dark:bg-gray-950 border-gray-200 dark:border-gray-700"
          
        >
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr 
                  className="border-b bg-gray-50 dark:bg-gray-900 border-gray-200 dark:border-gray-700"
                  
                >
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    Subprocessador
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    Tipo de Serviço
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    País/Região
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    Dados Processados
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    Avaliação de Risco
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-gray-400 dark:text-gray-500" >
                    Última Revisão
                  </th>
                </tr>
              </thead>
              <tbody>
                {subprocessors.map((sub, index) => (
                  <tr 
                    key={sub.id}
                    className={`border-b hover:bg-gray-50 transition-colors border-gray-200 dark:border-gray-700 ${index % 2 !== 0 ? 'bg-gray-50 dark:bg-gray-900' : ''}`}
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        <span className="font-medium text-sm text-gray-800 dark:text-gray-100" >
                          {sub.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span 
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-200/30"
                      >
                        {sub.service}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1.5">
                        <Globe className="w-3.5 h-3.5 text-gray-400 dark:text-gray-500"  />
                        <span className="text-sm text-gray-500 dark:text-gray-400" >
                          {sub.country}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-gray-500 dark:text-gray-400" >
                        {sub.dataTypes}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      {getRiskBadge(sub.risk)}
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-gray-500 dark:text-gray-400" >
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
          className="mt-4 p-4 rounded-md border bg-gray-200/20 border-wedo-cyan/20"
        >
          <p className="text-sm text-gray-500 dark:text-gray-400" >
            <strong>Transparência:</strong> Todos os subprocessadores passam por avaliação de segurança e possuem acordos de processamento de dados (DPA) assinados. Notificamos nossos clientes sobre qualquer alteração nesta lista com antecedência mínima de 30 dias.
          </p>
        </div>
      </div>
    </div>
  )
}
