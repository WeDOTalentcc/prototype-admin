import { NpsPageClient } from "./NpsPageClient"

interface Props {
  params: { token: string }
}

export default function NpsPage({ params }: Props) {
  return <NpsPageClient token={params.token} />
}
