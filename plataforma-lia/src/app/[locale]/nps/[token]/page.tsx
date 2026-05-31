import { NpsPageClient } from "./NpsPageClient"

interface Props {
  params: Promise<{ token: string }>
}

export default async function NpsPage({ params }: Props) {
  const { token } = await params
  return <NpsPageClient token={token} />
}
