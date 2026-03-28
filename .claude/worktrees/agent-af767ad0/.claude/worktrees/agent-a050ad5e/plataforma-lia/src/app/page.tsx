"use client"

import { Suspense } from "react"
import { DashboardApp } from "@/components/dashboard-app"
import { OnboardingController } from "@/components/onboarding/onboarding-controller"

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600 dark:text-gray-400">Carregando WeDO Talent...</p>
      </div>
    </div>
  )
}

export default function Page() {
  return (
    <Suspense fallback={<LoadingScreen />}>
      <OnboardingController>
        <DashboardApp />
      </OnboardingController>
    </Suspense>
  )
}
