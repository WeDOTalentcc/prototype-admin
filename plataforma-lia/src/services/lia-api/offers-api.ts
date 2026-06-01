"use client"

import type { OfferDraft, OfferDraftCreate, OfferDraftUpdate } from "@/types/offer"

const BASE = "/api/backend-proxy/offers"

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `API error ${res.status}`)
  }
  return res.json()
}

export const offersApi = {
  createDraft: (data: OfferDraftCreate) =>
    apiFetch<OfferDraft>(`${BASE}/drafts`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getDraft: (offerId: string) =>
    apiFetch<OfferDraft>(`${BASE}/drafts/${offerId}`),

  updateDraft: (offerId: string, data: OfferDraftUpdate) =>
    apiFetch<OfferDraft>(`${BASE}/drafts/${offerId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  sendAuto: (offerId: string) =>
    apiFetch<{ offer_id: string; status: string; email_log_id: string; sent_at: string; message: string }>(
      `${BASE}/drafts/${offerId}/send`,
      { method: "POST" }
    ),

  prepareManual: (offerId: string) =>
    apiFetch<{ offer_id: string; template_id?: string; subject_pre_filled: string; body_pre_filled: string; variables: Record<string, string>; message: string }>(
      `${BASE}/drafts/${offerId}/prepare-manual`,
      { method: "POST" }
    ),

  cancel: (offerId: string, reason?: string) =>
    apiFetch<void>(`${BASE}/drafts/${offerId}`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    }),
}
