import type { Metadata } from "next"
import StaffLayoutClient from "./StaffLayoutClient"

export const metadata: Metadata = {
  title: "WeDo Admin",
}

/**
 * Canonical layout para route group `(staff)/` — área provisória para
 * features que serão movidas para o admin externo WeDOTalent
 * (admin2.wedotalent.cc, repo `wedotalent-admin`) quando ele nascer.
 *
 * Plan canonical: ~/.claude/plans/jolly-roaming-moler.md
 * Audit base: ~/Documents/wedotalent_audit_2026-05-25/SETTINGS_COHERENCE_AUDIT.md
 *
 * Disciplina:
 * - Diretório espelha a futura estrutura do wedotalent-admin (copy fácil).
 * - Componentes da área vivem em src/components/_wedo_internal/.
 * - Gate de acesso: role === 'wedotalent_admin'. Não-staff recebe redirect.
 * - Não é exposto na Sidebar do produto — staff acessa por URL direto.
 */
export default function StaffLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <StaffLayoutClient>{children}</StaffLayoutClient>
}
