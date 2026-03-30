"use client"

import React, { useState, useEffect } from "react"
import { JobsPage } from "@/components/pages/jobs-page"

function LoadingSkeleton() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary p-6">
      <div className="animate-pulse motion-reduce:animate-none">
        <div className="h-8 w-48 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-4" />
        <div className="h-4 w-96 bg-gray-200 dark:bg-lia-bg-elevated rounded-md mb-8" />
        <div className="space-y-4">
          {[1,2,3,4,5].map(i => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-lia-bg-elevated rounded-md" />
          ))}
        </div>
      </div>
    </div>
  )
}

export default function JobsListPage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <LoadingSkeleton />
  }

  return <JobsPage />
}
