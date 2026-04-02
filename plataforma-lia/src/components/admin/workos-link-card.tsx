'use client'

import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Shield, ExternalLink, LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface WorkOSLinkCardProps {
  title: string
  description: string
  href: string
  icon?: LucideIcon
}

export const WorkOSLinkCard = React.forwardRef<
  HTMLDivElement,
  WorkOSLinkCardProps
>(({ title, description, href, icon: Icon = Shield }, ref) => {
  const handleOpenWorkOS = () => {
    window.open(href, '_blank', 'noopener,noreferrer')
  }

  return (
    <Card
      ref={ref}
      className={cn(
 'border-2 border-dashed border-lia-border-default',
        'hover:border-gray-900 dark:hover:border-gray-50',
        'transition-colors duration-200'
      )}
    >
      <CardContent className="flex items-center justify-between p-6">
        <div className="flex items-start gap-4 flex-1">
          <Icon className="h-5 w-5 text-lia-text-secondary mt-1 flex-shrink-0" />
          <div className="flex-1">
            <h3 className="font-semibold text-lia-text-primary">{title}</h3>
            <p className="text-sm text-lia-text-secondary mt-1">{description}</p>
          </div>
        </div>
        <Button
          onClick={handleOpenWorkOS}
          size="sm"
          className="ml-4 flex-shrink-0"
        >
          Abrir no WorkOS
          <ExternalLink />
        </Button>
      </CardContent>
    </Card>
  )
})

WorkOSLinkCard.displayName = 'WorkOSLinkCard'
