import { getRequestConfig } from 'next-intl/server'
import { routing } from './routing'
import { localeToMessages } from './config'
import type { Locale } from './config'

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale

  if (!locale || !routing.locales.includes(locale as Locale)) {
    locale = routing.defaultLocale
  }

  const messagesFile = localeToMessages[locale as Locale] || 'pt-BR'

  return {
    locale,
    messages: (await import(`../../messages/${messagesFile}.json`)).default,
  }
})
