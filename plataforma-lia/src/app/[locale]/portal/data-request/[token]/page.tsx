"use client"

import { useDataRequest } from "./_hooks/useDataRequest"
import { DataRequestForm } from "./_components/DataRequestForm"

export default function CandidatePortalPage() {
  const hook = useDataRequest()
  return <DataRequestForm hook={hook} />
}
