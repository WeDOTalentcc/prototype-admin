"use client"

import { useTriagemSession } from "./_hooks/useTriagemSession"
import { TriagemFlow } from "./_components/TriagemFlow"

export default function TriagemPage() {
  const hook = useTriagemSession()
  return <TriagemFlow hook={hook} />
}
