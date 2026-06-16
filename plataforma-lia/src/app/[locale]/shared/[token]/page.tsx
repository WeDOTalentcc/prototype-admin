'use client'

import { useSharedToken } from './_hooks/useSharedToken'
import { SharedContent } from './_components/SharedContent'

export default function SharedSearchPage() {
  const hook = useSharedToken()
  return <SharedContent hook={hook} />
}
