"use client"

import { Suspense } from "react"
import { DashboardApp } from "@/components/dashboard-app"
import { OnboardingController } from "@/components/onboarding/onboarding-controller"

function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin motion-reduce:animate-none rounded-full h-12 w-12 border-b-2 border-wedo-cyan/30 mx-auto mb-4"></div>
        <p className="lia-text-600 dark:text-lia-text-tertiary">Carregando WeDO Talent...</p>
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
