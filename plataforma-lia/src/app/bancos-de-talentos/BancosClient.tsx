"use client"

import React from "react"
import TalentPoolsTab from "@/components/pages-candidates/TalentPoolsTab"
import { useRouter } from "next/navigation"

export default function BancosClient() {
  const router = useRouter()
  return (
    <div className="h-full p-6">
      <TalentPoolsTab onSelectPool={(id) => router.push(`/bancos-de-talentos/${id}`)} />
    </div>
  )
}
