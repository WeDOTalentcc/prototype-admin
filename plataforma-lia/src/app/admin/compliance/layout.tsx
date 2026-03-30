"use client"

import React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import {
  Shield,
  ChevronRight,
  Award,
  FileCheck,
  Lock,
  AlertTriangle,
  Activity,
  ClipboardList
} from "lucide-react"

const complianceSections = [
  { 
    name: 'Dashboard', 
    href: '/admin/compliance', 
    icon: Shield,
    description: 'Visão geral de compliance'
  },
  { 
    name: 'Trust Center', 
    href: '/admin/compliance/trust-center', 
    icon: Award,
    description: 'Certificações e transparência'
  },
  { 
    name: 'Controles', 
    href: '/admin/compliance/controles', 
    icon: FileCheck,
    description: 'ISO 27001, SOC 2, SOX'
  },
  { 
    name: 'LGPD & Privacidade', 
    href: '/admin/compliance/lgpd', 
    icon: Lock,
    description: 'Proteção de dados'
  },
  { 
    name: 'Gestão de Riscos', 
    href: '/admin/compliance/riscos', 
    icon: AlertTriangle,
    description: 'Risk Register, BCN, Seguro'
  },
  { 
    name: 'Monitoramento', 
    href: '/admin/compliance/monitoramento', 
    icon: Activity,
    description: 'SOC/SIEM, Incidentes'
  },
  { 
    name: 'Sala de Auditoria', 
    href: '/admin/compliance/auditoria', 
    icon: ClipboardList,
    description: 'Logs, Bias, Exportação'
  },
]

export default function ComplianceLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  
  const isActive = (href: string) => {
    if (href === '/admin/compliance') {
      return pathname === '/admin/compliance'
    }
    return pathname.startsWith(href)
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
      <div 
        className="border-b bg-white dark:lia-bg-950 border-lia-border-subtle dark:border-lia-border-subtle"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex items-center gap-2 py-3 text-sm">
            <Link 
              href="/admin"
              className="hover:lia-text-900 dark:hover:lia-text-50 transition-colors motion-reduce:transition-none lia-text-400 dark:lia-text-500"
            >
              Admin
            </Link>
            <ChevronRight className="w-4 h-4 lia-text-400 dark:lia-text-500" />
            <div className="flex items-center gap-2">
              <span className="lia-text-800 dark:text-lia-text-primary">
                Compliance & Segurança
              </span>
              <Badge 
                variant="outline" 
                className="text-micro font-medium border-lia-border-default"
              >
                GLOBAL
              </Badge>
            </div>
          </nav>

          <div className="py-4">
            <div className="flex items-center gap-3">
              <div 
                className="w-12 h-12 rounded-md flex items-center justify-center bg-gray-200/30"
              >
                <Shield className="w-6 h-6 lia-text-600 dark:text-lia-text-tertiary" />
              </div>
              <div>
                <h1 
                  className="text-2xl font-semibold lia-text-800 dark:text-lia-text-primary"
                >
                  Compliance & Segurança
                </h1>
                <p className="text-sm lia-text-400 dark:lia-text-500">
                  Governança, controles e conformidade regulatória
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1 overflow-x-auto pb-px -mb-px">
            {complianceSections.map((section) => {
              const active = isActive(section.href)
              const Icon = section.icon
              return (
                <Link
                  key={section.href}
                  href={section.href}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                    active
                      ? "border-gray-900 dark:lia-border-50 lia-text-600 dark:text-lia-text-tertiary"
                      : "border-transparent hover:border-lia-border-default dark:hover:border-gray-600 lia-text-500 dark:text-lia-text-tertiary"
                  )}
                  title={section.description}
                >
                  <Icon className="w-4 h-4" />
                  {section.name}
                </Link>
              )
            })}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </div>
    </div>
  )
}
