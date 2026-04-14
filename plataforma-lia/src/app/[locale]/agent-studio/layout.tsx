import { getTranslations } from 'next-intl/server'

export async function generateMetadata() {
  const t = await getTranslations('agents.metadata')
  return {
    title: t('layoutTitle'),
    description: t('layoutDescription'),
  }
}

export default function Layout({ children }: { children: React.ReactNode }) {
  return <>{children}</>
}
