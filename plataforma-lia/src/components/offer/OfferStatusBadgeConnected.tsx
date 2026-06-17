"use client"

/**
 * OfferStatusBadgeConnected — fetches offer status for a candidate and renders OfferStatusBadge.
 *
 * Self-contained data-fetching wrapper. Renders nothing if no offer found.
 * staleTime=60s avoids N parallel requests per kanban refresh.
 *
 * Rules-of-hooks compliant: hook is unconditional at top level.
 */
import { useQuery } from "@tanstack/react-query"
import { OfferStatusBadge, type OfferStatusValue } from "./OfferStatusBadge"

interface OfferStatusData {
  offer_id: string
  status: OfferStatusValue
  candidate_viewed_at: string | null
  sent_at: string | null
  accepted_at: string | null
  declined_at: string | null
}

async function fetchOfferByCandidate(candidateId: string): Promise<OfferStatusData | null> {
  const res = await fetch(`/api/backend-proxy/offers/by-candidate/${candidateId}`)
  if (res.status === 404) return null
  if (!res.ok) return null
  const data = await res.json()
  return data
}

interface OfferStatusBadgeConnectedProps {
  candidateId: string
}

export function OfferStatusBadgeConnected({ candidateId }: OfferStatusBadgeConnectedProps) {
  const { data } = useQuery({
    queryKey: ["offer-by-candidate", candidateId],
    queryFn: () => fetchOfferByCandidate(candidateId),
    staleTime: 60_000,
    enabled: !!candidateId,
  })

  if (!data || data.status === "draft" || data.status === "cancelled") return null

  return (
    <OfferStatusBadge
      status={data.status}
      candidateViewed={!!data.candidate_viewed_at}
    />
  )
}
