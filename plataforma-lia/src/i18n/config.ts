export const locales = ['pt', 'en'] as const
export type Locale = (typeof locales)[number]
export const defaultLocale: Locale = 'pt'

export const localeNames: Record<Locale, string> = {
  pt: 'Português',
  en: 'English',
}

export const localeToMessages: Record<Locale, string> = {
  pt: 'pt-BR',
  en: 'en',
}
