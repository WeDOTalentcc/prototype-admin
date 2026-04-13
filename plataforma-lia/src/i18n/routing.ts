import { defineRouting } from 'next-intl/routing'
import { createNavigation } from 'next-intl/navigation'
import { locales, defaultLocale } from './config'

export const routing = defineRouting({
  locales,
  defaultLocale,
  localePrefix: 'always',
  pathnames: {
    '/': '/',
    '/login': {
      pt: '/login',
      en: '/login',
    },
    '/register': {
      pt: '/register',
      en: '/register',
    },
    '/vagas/[slug]': {
      pt: '/vagas/[slug]',
      en: '/jobs/[slug]',
    },
    '/funil': {
      pt: '/funil',
      en: '/pipeline',
    },
    '/funil-de-talentos': {
      pt: '/funil-de-talentos',
      en: '/talent-pipeline',
    },
    '/configuracoes': {
      pt: '/configuracoes',
      en: '/settings',
    },
    '/agent-studio': {
      pt: '/agent-studio',
      en: '/agent-studio',
    },
    '/chat': {
      pt: '/chat',
      en: '/chat',
    },
    '/tasks': {
      pt: '/tasks',
      en: '/tasks',
    },
    '/forgot-password': {
      pt: '/forgot-password',
      en: '/forgot-password',
    },
    '/reset-password': {
      pt: '/reset-password',
      en: '/reset-password',
    },
    '/privacidade': {
      pt: '/privacidade',
      en: '/privacy',
    },
    '/portal': {
      pt: '/portal',
      en: '/portal',
    },
    '/shared': {
      pt: '/shared',
      en: '/shared',
    },
    '/ajuda': {
      pt: '/ajuda',
      en: '/help',
    },
    '/upgrade': {
      pt: '/upgrade',
      en: '/upgrade',
    },
    '/bancos-de-talentos': {
      pt: '/bancos-de-talentos',
      en: '/talent-pools',
    },
    '/trust': {
      pt: '/trust',
      en: '/trust',
    },
    '/design-system': {
      pt: '/design-system',
      en: '/design-system',
    },
  },
})

export const { Link, redirect, usePathname, useRouter, getPathname } = createNavigation(routing)
