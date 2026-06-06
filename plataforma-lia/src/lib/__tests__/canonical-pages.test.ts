import { describe, expect, it } from "vitest";
import {
  CANONICAL_PAGES,
  canonicalPageToUrl,
  routeToCanonicalPage,
} from "@/lib/canonical-pages";

/**
 * Regressão 2026-06-06: o handler navigate_to do chat (useUIAction)
 * empurrava o NOME canônico cru ("vagas") -> /pt/vagas = 404 (a lista real
 * é /jobs; /vagas só tem [slug]). canonicalPageToUrl é a fonte única
 * page->rota; este teste pina o contrato que o useUIAction passou a
 * consumir (e o suporte a id em páginas de detalhe).
 */
describe("canonicalPageToUrl — mapa page->rota (fix 404 navigate_to)", () => {
  it("VAGAS resolve pra rota real /jobs, NUNCA /vagas (404)", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.VAGAS, "pt")).toBe("/pt/jobs");
    expect(canonicalPageToUrl(CANONICAL_PAGES.VAGAS, "pt")).not.toBe(
      "/pt/vagas",
    );
  });

  it("respeita o locale ativo", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.VAGAS, "en")).toBe("/en/jobs");
    expect(canonicalPageToUrl(CANONICAL_PAGES.FUNIL_TALENTOS, "en")).toBe(
      "/en/funil-de-talentos",
    );
  });

  it("slugs divergentes do nome canônico resolvem certo", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.FUNIL_TALENTOS, "pt")).toBe(
      "/pt/funil-de-talentos",
    );
    expect(canonicalPageToUrl(CANONICAL_PAGES.AGENT_STUDIO, "pt")).toBe(
      "/pt/agent-studio",
    );
    expect(canonicalPageToUrl(CANONICAL_PAGES.BANCOS_TALENTOS, "pt")).toBe(
      "/pt/bancos-de-talentos",
    );
    expect(canonicalPageToUrl(CANONICAL_PAGES.RECRUTAR, "pt")).toBe(
      "/pt/recrutar",
    );
  });

  it("vaga_detalhe COM id -> /jobs/{id}; sem id -> null", () => {
    expect(
      canonicalPageToUrl(CANONICAL_PAGES.VAGA_DETALHE, "pt", "V0003"),
    ).toBe("/pt/jobs/V0003");
    expect(canonicalPageToUrl(CANONICAL_PAGES.VAGA_DETALHE, "pt")).toBeNull();
  });

  it("candidato_detalhe COM id -> /funil-de-talentos/candidato/{id}", () => {
    expect(
      canonicalPageToUrl(CANONICAL_PAGES.CANDIDATO_DETALHE, "pt", "abc123"),
    ).toBe("/pt/funil-de-talentos/candidato/abc123");
  });

  it("só GENERAL e detalhes-sem-id retornam null (falha-soft, não 404)", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.GENERAL, "pt")).toBeNull();
    expect(canonicalPageToUrl(CANONICAL_PAGES.VAGA_DETALHE, "pt")).toBeNull();
    expect(canonicalPageToUrl(CANONICAL_PAGES.CANDIDATO_DETALHE, "pt")).toBeNull();
  });

  it("round-trip: a URL gerada volta pra mesma canonical page", () => {
    const vagasUrl = canonicalPageToUrl(CANONICAL_PAGES.VAGAS, "pt");
    expect(vagasUrl).not.toBeNull();
    expect(routeToCanonicalPage(vagasUrl as string)).toBe(CANONICAL_PAGES.VAGAS);

    const detailUrl = canonicalPageToUrl(
      CANONICAL_PAGES.VAGA_DETALHE,
      "pt",
      "11111111-1111-1111-1111-111111111111",
    );
    expect(detailUrl).not.toBeNull();
    expect(routeToCanonicalPage(detailUrl as string)).toBe(
      CANONICAL_PAGES.VAGA_DETALHE,
    );
  });
});


/**
 * Fase A (2026-06-06): navegação universal da LIA. Toda página exposta ao
 * recrutador precisa de rota real (senão o agente promete e o FE não cumpre).
 * dashboard→home (DashboardApp), pipeline_kanban→/recrutar (visão global do
 * pipeline), + 3 páginas extra (decisão Paulo 2026-06-06).
 */
describe("Fase A — cobertura completa de páginas (navegação universal LIA)", () => {
  it("dashboard resolve pra home /{loc}/ (DashboardApp é a home)", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.DASHBOARD, "pt")).toBe("/pt/");
  });

  it("pipeline_kanban resolve pra /recrutar (visão global do pipeline)", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.PIPELINE_KANBAN, "pt")).toBe(
      "/pt/recrutar",
    );
  });

  it("páginas extra expostas têm rota real", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.AGENTS_MARKETPLACE, "pt")).toBe(
      "/pt/agents/marketplace",
    );
    expect(canonicalPageToUrl(CANONICAL_PAGES.AI_CREDITS, "pt")).toBe(
      "/pt/configuracoes/ai-credits",
    );
    expect(canonicalPageToUrl(CANONICAL_PAGES.INTEGRACOES_ATS, "pt")).toBe(
      "/pt/integracoes-ats",
    );
  });

  it("round-trip das páginas extra (URL volta pra mesma canonical)", () => {
    for (const p of [
      CANONICAL_PAGES.AGENTS_MARKETPLACE,
      CANONICAL_PAGES.AI_CREDITS,
      CANONICAL_PAGES.INTEGRACOES_ATS,
    ]) {
      const url = canonicalPageToUrl(p, "pt");
      expect(url).not.toBeNull();
      expect(routeToCanonicalPage(url as string)).toBe(p);
    }
  });

  it("INVARIANTE: toda página exposta (não-detalhe, não-general) tem rota não-null", () => {
    const needsId = new Set<string>([
      CANONICAL_PAGES.VAGA_DETALHE,
      CANONICAL_PAGES.CANDIDATO_DETALHE,
    ]);
    for (const page of Object.values(CANONICAL_PAGES)) {
      if (page === CANONICAL_PAGES.GENERAL) continue;
      if (needsId.has(page)) continue;
      expect(canonicalPageToUrl(page, "pt")).not.toBeNull();
    }
  });
});
