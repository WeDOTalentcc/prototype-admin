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

  it("pages sem URL canônica retornam null (falha-soft, não 404)", () => {
    expect(canonicalPageToUrl(CANONICAL_PAGES.PIPELINE_KANBAN, "pt")).toBeNull();
    expect(canonicalPageToUrl(CANONICAL_PAGES.DASHBOARD, "pt")).toBeNull();
    expect(canonicalPageToUrl(CANONICAL_PAGES.GENERAL, "pt")).toBeNull();
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
