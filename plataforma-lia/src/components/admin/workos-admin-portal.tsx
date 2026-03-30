'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { ExternalLink, Settings } from 'lucide-react'

interface WorkOSAdminPortalProps {
  organizationId?: string
  triggerText?: string
  variant?: 'button' | 'link'
}

export function WorkOSAdminPortal({ 
  organizationId, 
  triggerText = 'Admin Portal',
  variant = 'button'
}: WorkOSAdminPortalProps) {
  const [isOpen, setIsOpen] = useState(false)
  
  const portalUrl = organizationId 
    ? `https://dashboard.workos.com/admin-portal?organization_id=${organizationId}`
    : 'https://dashboard.workos.com/admin-portal'

  const handleOpenExternal = () => {
    window.open(portalUrl, '_blank', 'noopener,noreferrer')
    setIsOpen(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        {variant === 'button' ? (
          <Button variant="outline" className="gap-2">
            <Settings className="h-4 w-4" />
            {triggerText}
          </Button>
        ) : (
          <button className="text-gray-600 dark:text-lia-text-tertiary hover:underline flex items-center gap-1 text-sm">
            <Settings className="h-3 w-3" />
            {triggerText}
          </button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-4xl h-[80vh]">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle>WorkOS Admin Portal</DialogTitle>
              <DialogDescription>
                Configure SSO e Directory Sync para sua organização
              </DialogDescription>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleOpenExternal}
              className="gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Abrir em nova aba
            </Button>
          </div>
        </DialogHeader>
        <div className="flex-1 mt-4 rounded-md overflow-hidden border">
          <iframe
            src={portalUrl}
            className="w-full h-full min-h-[500px]"
            title="WorkOS Admin Portal"
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          />
        </div>
        <p className="text-xs lia-text-secondary mt-2">
          Nota: Algumas funcionalidades podem requerer autenticação no WorkOS Dashboard.
        </p>
      </DialogContent>
    </Dialog>
  )
}
