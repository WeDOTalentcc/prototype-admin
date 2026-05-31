import { AlignPageClient } from "./AlignPageClient"

interface Props {
  params: Promise<{ token: string }>
}

export default async function AlignPage({ params }: Props) {
  const { token } = await params
  return <AlignPageClient token={token} />
}
