"use client"
import React, { useState } from "react"
import TalentPoolsTab from "@/components/pages-candidates/TalentPoolsTab"

export default function BancosClient() {
  const [openPoolId, setOpenPoolId] = useState<string | null>(null)

  return (
    <div className="h-full p-6">
      <TalentPoolsTab
        onSelectPool={(id) => setOpenPoolId(id)}
        openPoolId={openPoolId}
        onClosePool={() => setOpenPoolId(null)}
      />
    </div>
  )
}
