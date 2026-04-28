/**
 * Task #894 — teste irmão de `use-ui-action.test.ts`.
 *
 * O teste de `useUIAction` valida que o produtor monta a URL canônica
 * (`/configuracoes?section=<id>`). Aqui validamos o outro lado do
 * circuito: o consumidor (`SettingsPageEnhanced`) parsea o `searchParams`
 * e abre a tab destino, em vez de cair na default `minha-empresa`.
 *
 * A lógica de parsing vive em `resolveSettingsTarget`, exportada da
 * página, exatamente para que este teste possa cobri-la sem precisar
 * montar todo o monolito (8 hubs lazy-loaded, fetch de progresso, etc.).
 */

import { describe, expect, it } from "vitest";
import { resolveSettingsTarget } from "@/lib/settings/resolve-settings-target";

describe("resolveSettingsTarget — page parsea o destino do searchParams", () => {
  it("`?section=integrations` (CTA do job-publish-modal) abre tab Integrações", () => {
    const params = new URLSearchParams("section=integrations");
    expect(resolveSettingsTarget(params)).toEqual({
      section: "integrations",
      subsection: "",
      field: null,
    });
  });

  it("`?section=webhooks` (Task #895) abre tab Webhooks", () => {
    const params = new URLSearchParams("section=webhooks");
    expect(resolveSettingsTarget(params)).toEqual({
      section: "webhooks",
      subsection: "",
      field: null,
    });
  });

  it("`?section=pipeline` (card hiring-policy do chat-workflow-reels) abre tab Pipeline", () => {
    const params = new URLSearchParams("section=pipeline");
    expect(resolveSettingsTarget(params).section).toBe("pipeline");
  });

  it("`?section=templates-assinatura` (card email-templates) abre tab Templates", () => {
    const params = new URLSearchParams("section=templates-assinatura");
    expect(resolveSettingsTarget(params).section).toBe("templates-assinatura");
  });

  it("alias `?section=alertas` resolve para `comunicacao-alertas`", () => {
    const params = new URLSearchParams("section=alertas");
    expect(resolveSettingsTarget(params).section).toBe("comunicacao-alertas");
  });

  it("alias `?section=integracoes` (legado) resolve para `integrations`", () => {
    const params = new URLSearchParams("section=integracoes");
    expect(resolveSettingsTarget(params).section).toBe("integrations");
  });

  it("section desconhecida não abre tab fantasma — retorna `null`", () => {
    const params = new URLSearchParams("section=qualquer-coisa-inexistente");
    expect(resolveSettingsTarget(params).section).toBeNull();
  });

  it("sem `?section=`, retorna `null` (mantém default da página)", () => {
    const params = new URLSearchParams("");
    expect(resolveSettingsTarget(params).section).toBeNull();
  });

  it("`?section=fairness-compliance&subsection=lgpd-candidatos` abre subsection válida", () => {
    const params = new URLSearchParams(
      "section=fairness-compliance&subsection=lgpd-candidatos",
    );
    expect(resolveSettingsTarget(params)).toEqual({
      section: "fairness-compliance",
      subsection: "lgpd-candidatos",
      field: null,
    });
  });

  it("subsection desconhecida é descartada (não polui state)", () => {
    const params = new URLSearchParams(
      "section=fairness-compliance&subsection=fake",
    );
    expect(resolveSettingsTarget(params).subsection).toBe("");
  });

  it("`?field=` (Task #712) é preservado para scroll-into-view", () => {
    const params = new URLSearchParams("section=minha-empresa&field=cnpj");
    expect(resolveSettingsTarget(params).field).toBe("cnpj");
  });

  it("`?field=` continua funcionando mesmo sem `?section=`", () => {
    const params = new URLSearchParams("field=cnpj");
    expect(resolveSettingsTarget(params)).toEqual({
      section: null,
      subsection: "",
      field: "cnpj",
    });
  });

  it("params null/undefined retornam target vazio (sem crash)", () => {
    expect(resolveSettingsTarget(null)).toEqual({
      section: null,
      subsection: "",
      field: null,
    });
    expect(resolveSettingsTarget(undefined)).toEqual({
      section: null,
      subsection: "",
      field: null,
    });
  });
});
