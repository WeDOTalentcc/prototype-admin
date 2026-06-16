import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        // Bloquear rotas autenticadas de indexação (são privadas)
        disallow: [
          '/api/',
          '/login',
          '/register',
          '/forgot-password',
          '/reset-password',
          '/shared/',
        ],
        allow: [
          '/',
          '/vagas/', // página pública de vagas
        ],
      },
    ],
    sitemap: `${process.env.NEXT_PUBLIC_APP_URL || 'https://app.wedotalent.com'}/sitemap.xml`,
  }
}
