"use client"

import React from "react"
import Link from "next/link"
import { BadgeCheck, Download, CheckCircle2, Clock, XCircle, ArrowLeft } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"

const certifications = [
  { id: 1, name: 'ISO 27001:2022', status: 'active', issued: '2024-03-15', expires: '2027-03-14', issuer: 'BSI Group', hasDocument: true },
  { id: 2, name: 'SOC 2 Type II', status: 'active', issued: '2024-06-01', expires: '2025-05-31', issuer: 'Deloitte', hasDocument: true },
  { id: 3, name: 'LGPD Compliance', status: 'active', issued: '2024-01-01', expires: '2025-12-31', issuer: 'Interno', hasDocument: false },
]

function getStatusBadge(status: string) {
  switch (status) {
    case 'active':
      return <Badge variant="success" className="gap-1"><CheckCircle2 className="w-3.5 h-3.5" />Ativo</Badge>
    case 'renewing':
      return <Badge variant="warning" className="gap-1"><Clock className="w-3.5 h-3.5" />Em Renovação</Badge>
    case 'expired':
      return <Badge variant="danger" className="gap-1"><XCircle className="w-3.5 h-3.5" />Expirado</Badge>
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

export default function CertificacoesPage() {
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
            <BadgeCheck className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary"
              
            >
              Lista de Certificações
            </h1>
            <p className="text-sm text-lia-text-tertiary dark:text-lia-text-secondary" >
              Certificações obtidas e em andamento
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
                    Certificação
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Status
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Data de Emissão
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Data de Validade
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Organismo Certificador
                  </th>
                  <th className="text-center px-4 py-3 text-xs font-medium uppercase tracking-wider text-lia-text-tertiary dark:text-lia-text-secondary" >
                    Ação
                  </th>
                </tr>
              </thead>
              <tbody>
                {certifications.map((cert, index) => (
                  <tr 
                    key={cert.id}
                    className={`border-b hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none border-lia-border-subtle dark:border-lia-border-subtle ${index % 2 !== 0 ? 'bg-lia-bg-secondary dark:bg-lia-bg-primary' : ''}`}
                  >
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <BadgeCheck className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
                        <span className="font-medium text-sm text-lia-text-primary dark:text-lia-text-primary" >
                          {cert.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      {getStatusBadge(cert.status)}
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                        {formatDate(cert.issued)}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                        {formatDate(cert.expires)}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <span className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary" >
                        {cert.issuer}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-center">
                      {cert.hasDocument ? (
                        <button 
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-white hover:opacity-90 transition-opacity motion-reduce:transition-none bg-lia-btn-primary-bg"
                          onClick={() => toast.info('Funcionalidade de download em implementação', { description: 'Em breve você poderá baixar os certificados.' })}
                        >
                          <Download className="w-3.5 h-3.5" />
                          Download
                        </button>
                      ) : (
                        <span className="text-xs italic text-lia-text-tertiary dark:text-lia-text-secondary" >
                          Documento interno
                        </span>
                      )}
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
            <strong>Nota:</strong> Para solicitar cópias oficiais de certificados ou relatórios de auditoria, entre em contato com nossa equipe de compliance através do email <span className="text-lia-text-primary">compliance@lia.ai</span>
          </p>
        </div>
      </div>
    </div>
  )
}
