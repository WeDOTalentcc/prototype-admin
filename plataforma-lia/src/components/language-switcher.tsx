"use client"

import { useLocale } from 'next-intl'
import { useRouter, usePathname } from '@/i18n/routing'
import { useTransition } from 'react'
import { Globe } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { Locale } from '@/i18n/config'
import { localeNames } from '@/i18n/config'

export function LanguageSwitcher({ collapsed = false }: { collapsed?: boolean }) {
  const locale = useLocale() as Locale
  const router = useRouter()
  const pathname = usePathname()
  const [isPending, startTransition] = useTransition()

  const nextLocale: Locale = locale === 'pt' ? 'en' : 'pt'

  function handleSwitch() {
    document.cookie = `NEXT_LOCALE=${nextLocale};path=/;max-age=${60 * 60 * 24 * 365};samesite=lax`

    startTransition(() => {
      router.replace(pathname, { locale: nextLocale })
    })
  }

  const label = locale.toUpperCase()
  const title = `${localeNames[locale]} → ${localeNames[nextLocale]}`

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={handleSwitch}
      disabled={isPending}
      className={cn(
        "p-0 text-lia-text-primary hover:bg-lia-interactive-hover font-medium",
        collapsed ? "h-6 w-6" : "h-6 gap-1 px-1.5"
      )}
      title={title}
    >
      <Globe className="w-3 h-3 flex-shrink-0" />
      {!collapsed && (
        <span className="text-[10px] tracking-wide font-semibold leading-none">
          {label}
        </span>
      )}
    </Button>
  )
}
