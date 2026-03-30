"use client"

import React from "react"
import Link from "next/link"
import { Download, FileText, ArrowLeft, Lock, Mail } from "lucide-react"
import { toast } from "sonner"

const resources = [
  { 
    id: 1, 
    name: 'Política de Privacidade', 
    type: 'PDF', 
    description: 'Como coletamos, usamos e protegemos seus dados pessoais',
    downloadable: true,
    icon: FileText
  },
  { 
    id: 2, 
    name: 'Política de Segurança da Informação', 
    type: 'PDF', 
    description: 'Nossos controles e práticas de segurança da informação',
    downloadable: true,
    icon: Lock
  },
  { 
    id: 3, 
    name: 'Termos de Uso', 
    type: 'PDF', 
    description: 'Termos e condições de uso da plataforma LIA',
    downloadable: true,
    icon: FileText
  },
  { 
    id: 4, 
    name: 'Adendo de Processamento de Dados (DPA)', 
    type: 'PDF', 
    description: 'Acordo de processamento de dados para clientes',
    downloadable: true,
    icon: FileText
  },
  { 
    id: 5, 
    name: 'Relatório SOC 2', 
    type: 'PDF', 
    description: 'Relatório de auditoria SOC 2 Type II mais recente',
    downloadable: false,
    requestRequired: true,
    icon: Lock
  },
  { 
    id: 6, 
    name: 'Certificado ISO 27001', 
    type: 'PDF', 
    description: 'Certificado oficial ISO 27001:2022',
    downloadable: false,
    requestRequired: true,
    icon: Lock
  },
]

export default function RecursosPage() {
  const handleDownload = (resourceName: string) => {
    toast.success(`Download de "${resourceName}" iniciado!`, {
      description: 'O arquivo será baixado em instantes.'
    })
  }

  const handleRequest = (resourceName: string) => {
    toast.success(`Solicitação de "${resourceName}" enviada!`, {
      description: 'Nossa equipe entrará em contato em breve.'
    })
  }

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4">
          <Link 
            href="/admin/compliance/trust-center"
            className="inline-flex items-center gap-1 text-sm hover:underline lia-text-700"
          >
            <ArrowLeft className="w-4 h-4" />
            Voltar ao Trust Center
          </Link>
        </div>

        <div className="flex items-center gap-3 mb-6">
          <div 
            className="w-10 h-10 rounded-md flex items-center justify-center bg-gray-200/30"
          >
            <Download className="w-5 h-5 lia-text-600 dark:text-lia-text-tertiary" />
          </div>
          <div>
            <h1 
              className="text-xl font-semibold lia-text-800 dark:text-lia-text-primary"
              
            >
              Recursos Downloadáveis
            </h1>
            <p className="text-sm lia-text-400 dark:lia-text-500" >
              Documentos, políticas e materiais de compliance
            </p>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {resources.map((resource) => {
            const IconComponent = resource.icon
            return (
              <div 
                key={resource.id}
                className="rounded-md border p-4 hover:transition-shadow bg-white dark:lia-bg-950 border-lia-border-subtle dark:border-lia-border-subtle"
                
              >
                <div className="flex items-start gap-4">
                  <div 
                    className="w-10 h-10 rounded-md flex items-center justify-center shrink-0"
                    style={{backgroundColor: resource.requestRequired ? 'var(--status-warning-bg)' : 'var(--gray-bg-30)'}}
                  >
                    <IconComponent 
                      className="w-5 h-5" 
                      style={{color: resource.requestRequired ? 'var(--status-warning)' : 'var(--gray-600)'}}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-sm lia-text-800 dark:text-lia-text-primary" >
                        {resource.name}
                      </h3>
                      <span 
                        className="px-1.5 py-0.5 rounded-md text-xs font-medium bg-gray-50 dark:bg-lia-bg-primary lia-text-400 dark:lia-text-500"
                        
                      >
                        {resource.type}
                      </span>
                    </div>
                    <p className="text-xs mb-3 lia-text-400 dark:lia-text-500" >
                      {resource.description}
                    </p>
                    {resource.downloadable ? (
                      <button 
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-white hover:opacity-90 transition-opacity bg-gray-900"
                        onClick={() => handleDownload(resource.name)}
                      >
                        <Download className="w-3.5 h-3.5" />
                        Download
                      </button>
                    ) : (
                      <button 
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium border hover:bg-gray-50 transition-colors text-status-warning" style={{
                          borderColor: 'var(--status-warning)'
                        }}
                        onClick={() => handleRequest(resource.name)}
                      >
                        <Mail className="w-3.5 h-3.5" />
                        Solicitar Acesso
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div 
          className="mt-6 p-4 rounded-md border bg-status-warning-bg border-status-warning-border-light"
        >
          <div className="flex items-start gap-3">
            <Lock className="w-5 h-5 shrink-0 mt-0.5 text-status-warning" />
            <div>
              <h4 className="font-medium text-sm mb-1 lia-text-800 dark:text-lia-text-primary" >
                Documentos com Acesso Restrito
              </h4>
              <p className="text-sm lia-text-500 dark:text-lia-text-tertiary" >
                Alguns documentos requerem solicitação prévia e são disponibilizados apenas para clientes e parceiros após assinatura de NDA. 
                Para solicitar acesso, entre em contato com <span className="lia-text-700">compliance@lia.ai</span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
