/**
 * E2E — Task #1149 (T-1129 sealing) — Multi-tenant Ownership end-to-end.
 *
 * Cobre as 4 garantias de ownership entregues pelas sub-tasks S2 (gate
 * `_require_company_id`), S3 (cache Redis namespaced), S5 (webhook
 * ownership) e S6 (ES tenant filter) das tasks #1129a..f. Cada cenário
 * abaixo é red-team: tenant B autenticado tenta acessar / forjar /
 * poluir cache / vazar busca cruzando com tenant A.
 *
 * Sentinelas associadas (offline):
 *   - `lia-agent-system/tests/integration/security/`
 *     `test_multi_tenant_ownership_inventory_t_1129.py` (S9).
 *   - Eval gate: `eval/golden/multi_tenant_ownership.jsonl` (S8).
 *
 * Hardening pós-review (code_review REJECTED v1):
 *   - B2 agora exige HTTP **403 estrito** (mismatch de ownership, não
 *     401 unauth) e autentica como tenant B antes do POST cruzado.
 *   - B3 falha se NENHUMA das duas evidências de isolamento estiver
 *     presente (header de cache distinto OU corpo com tenant correto).
 *   - B4 semeia um **candidato exclusivo** do tenant A (não um marker
 *     em título de vaga) e exige que tenant B autenticado veja 0 hits.
 */
import { test, expect, type Page, type APIRequestContext } from "@playwright/test";

type TenantCreds = {
  email: string;
  password: string;
  companyId: string;
};

const TENANT_A: TenantCreds = {
  email: process.env.E2E_TENANT_A_EMAIL ?? "recruiter-a@demo-a.lia.test",
  password: process.env.E2E_TENANT_A_PASSWORD ?? "DemoA!2026",
  companyId:
    process.env.E2E_TENANT_A_COMPANY_ID ??
    "00000000-0000-4000-a000-000000000001",
};

const TENANT_B: TenantCreds = {
  email: process.env.E2E_TENANT_B_EMAIL ?? "recruiter-b@demo-b.lia.test",
  password: process.env.E2E_TENANT_B_PASSWORD ?? "DemoB!2026",
  companyId:
    process.env.E2E_TENANT_B_COMPANY_ID ??
    "00000000-0000-4000-a000-000000000002",
};

async function loginUI(page: Page, creds: TenantCreds): Promise<void> {
  await page.goto("/login");
  await page.getByLabel(/e-?mail/i).fill(creds.email);
  await page.getByLabel(/senha|password/i).fill(creds.password);
  await page.getByRole("button", { name: /entrar|login/i }).click();
  await page.waitForURL(/\/(dashboard|chat|configuracoes|funil-de-talentos)/, {
    timeout: 30_000,
  });
}

async function loginAPI(
  request: APIRequestContext,
  creds: TenantCreds,
): Promise<void> {
  // Reuses the dev/WorkOS password flow; cookies are stored in the
  // request context for the rest of the test.
  const r = await request.post("/api/v1/auth/login", {
    data: { email: creds.email, password: creds.password },
  });
  expect(
    [200, 201, 204],
    `login API tenant ${creds.companyId} → ${r.status()} (sem credenciais válidas a spec não pode rodar)`,
  ).toContain(r.status());
}

async function logoutUI(page: Page): Promise<void> {
  await page.context().clearCookies();
}

async function createJobAsTenantA(
  page: Page,
): Promise<{ jobId: string; uniqueMarker: string }> {
  const uniqueMarker = `T1129-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const resp = await page.request.post("/api/v1/jobs", {
    data: {
      title: `Backend Eng (${uniqueMarker})`,
      description: "Vaga T-1129 sealing red-team.",
      company_id: TENANT_A.companyId,
    },
  });
  expect(resp.status(), `POST /api/v1/jobs (tenant A) → ${resp.status()}`).toBe(
    201,
  );
  const body = (await resp.json()) as { id: string };
  return { jobId: body.id, uniqueMarker };
}

async function seedTenantAExclusiveCandidate(
  page: Page,
  jobId: string,
): Promise<{ candidateId: string; uniqueName: string }> {
  const uniqueName = `Candidato-T1129-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
  const resp = await page.request.post("/api/v1/candidates", {
    data: {
      full_name: uniqueName,
      email: `${uniqueName.toLowerCase()}@example-tenant-a.test`,
      company_id: TENANT_A.companyId,
      job_id: jobId,
    },
  });
  expect(
    [200, 201],
    `POST /api/v1/candidates (tenant A) → ${resp.status()}`,
  ).toContain(resp.status());
  const body = (await resp.json()) as { id: string };
  // Allow ES indexing pipeline a moment to catch up.
  await page.waitForTimeout(1500);
  return { candidateId: body.id, uniqueName };
}

test.describe("T-1129 — Multi-tenant ownership (red-team sealing)", () => {
  test.describe.configure({ mode: "serial" });

  let jobIdFromA: string;
  let uniqueCandidateName: string;

  test("B1 — vaga criada por tenant A retorna 403/404 para tenant B autenticado", async ({
    page,
  }) => {
    await loginUI(page, TENANT_A);
    const { jobId } = await createJobAsTenantA(page);
    const seeded = await seedTenantAExclusiveCandidate(page, jobId);
    jobIdFromA = jobId;
    uniqueCandidateName = seeded.uniqueName;
    await logoutUI(page);

    await loginUI(page, TENANT_B);
    const resp = await page.request.get(`/api/v1/jobs/${jobIdFromA}`);
    expect(
      [403, 404],
      `tenant B GET /jobs/${jobIdFromA} deve ser 403/404, veio ${resp.status()}`,
    ).toContain(resp.status());
  });

  test("B2 — webhook Teams autenticado como B com X-Company-ID=A retorna 403 estrito", async ({
    playwright,
  }) => {
    // Autentica COMO TENANT B antes do POST cruzado — sem isso a falha
    // poderia ser 401 (auth missing) em vez de 403 (ownership mismatch),
    // o que NÃO prova o gate de ownership.
    const ctx = await playwright.request.newContext();
    await loginAPI(ctx, TENANT_B);

    const resp = await ctx.post("/api/v1/teams/webhook", {
      headers: {
        "X-Company-ID": TENANT_A.companyId,
        "X-Teams-Bot-Tenant": TENANT_B.companyId,
        "Content-Type": "application/json",
      },
      data: {
        company_id: TENANT_A.companyId,
        conversation: { id: "test-conv-1129" },
        from: { id: "bot-tenant-b" },
        text: "T-1129 red-team",
      },
    });
    // Strict: ownership mismatch é 403. 401 indicaria ausência de auth
    // (não estamos provando o gate); 200/2xx indicaria leak.
    expect(
      resp.status(),
      `Teams webhook cross-tenant deve ser 403 (ownership mismatch), veio ${resp.status()}`,
    ).toBe(403);
    await ctx.dispose();
  });

  test("B3 — cache Redis isolado: mesma pergunta em dois tenants NÃO compartilha resposta", async ({
    browser,
  }) => {
    // Determinismo (pós code_review v3): a prova de isolamento de cache
    // PRECISA vir de evidência determinística emitida pelo backend.
    // O bug que estamos selando é "tenant B recebe a resposta cacheada de
    // tenant A para a mesma pergunta" — i.e. o padrão A:MISS → B:HIT em
    // chaves NÃO particionadas.
    //
    // Por isso a asserção principal exige UM destes (ordem de força):
    //   (E1) `x-cache-key` distinto entre A e B   ← prova direta de
    //         particionamento (cache key contém company_id namespace).
    //   (E2) `x-tenant-cache-namespace` distinto  ← header debug emitido
    //         pelo backend tenant-namespaced (Task #1129c).
    //   (E3) Ambos respondem A:MISS + B:MISS      ← cache não foi
    //         compartilhado (segunda chamada não achou a primeira).
    //
    // Padrões EXPLICITAMENTE PROIBIDOS (qualquer um falha o teste):
    //   (P1) A:MISS + B:HIT sem cache-key distinto → vazamento clássico.
    //   (P2) Corpo de B contém company_id de A (ou vice-versa).

    const ctxA = await browser.newContext();
    const pageA = await ctxA.newPage();
    await loginUI(pageA, TENANT_A);
    await pageA.goto("/chat");
    await pageA.getByTestId("lia-chat-input").fill("criar vaga de backend");
    const respPromiseA = pageA.waitForResponse((r) =>
      /\/chat|orchestrated_job_chat|messages/.test(r.url()),
    );
    await pageA.keyboard.press("Enter");
    const respA = await respPromiseA;
    const headersA = respA.headers();
    const cacheA = (headersA["x-cache"] ?? "").toUpperCase();
    const cacheKeyA = headersA["x-cache-key"] ?? "";
    const nsA = headersA["x-tenant-cache-namespace"] ?? "";
    const bodyA = await respA.text();

    const ctxB = await browser.newContext();
    const pageB = await ctxB.newPage();
    await loginUI(pageB, TENANT_B);
    await pageB.goto("/chat");
    await pageB.getByTestId("lia-chat-input").fill("criar vaga de backend");
    const respPromiseB = pageB.waitForResponse((r) =>
      /\/chat|orchestrated_job_chat|messages/.test(r.url()),
    );
    await pageB.keyboard.press("Enter");
    const respB = await respPromiseB;
    const headersB = respB.headers();
    const cacheB = (headersB["x-cache"] ?? "").toUpperCase();
    const cacheKeyB = headersB["x-cache-key"] ?? "";
    const nsB = headersB["x-tenant-cache-namespace"] ?? "";
    const bodyB = await respB.text();

    const distinctCacheKeys =
      cacheKeyA !== "" && cacheKeyB !== "" && cacheKeyA !== cacheKeyB;
    const distinctNamespaces = nsA !== "" && nsB !== "" && nsA !== nsB;
    const bothMiss = cacheA === "MISS" && cacheB === "MISS";

    // ---- (P1) Bloqueio determinístico do padrão de leak clássico. ----
    const aMissBHit = cacheA === "MISS" && cacheB === "HIT";
    expect(
      aMissBHit && !distinctCacheKeys && !distinctNamespaces,
      `LEAK DETECTADO (P1): tenant A=MISS + tenant B=HIT com mesma cache-key. ` +
        `cache-key A='${cacheKeyA}' B='${cacheKeyB}'; ` +
        `namespace A='${nsA}' B='${nsB}'. ` +
        `Isso significa que B leu o cache populado por A — cross-tenant cache poisoning. ` +
        `Verifique app/orchestrator/semantic_cache.py + tenant_namespaced_key (Task #1129c).`,
    ).toBe(false);

    // ---- Evidência determinística mínima ----
    expect(
      distinctCacheKeys || distinctNamespaces || bothMiss,
      `Evidência determinística de isolamento de cache ausente:\n` +
        `  x-cache-key A='${cacheKeyA}' B='${cacheKeyB}' (distinct=${distinctCacheKeys})\n` +
        `  x-tenant-cache-namespace A='${nsA}' B='${nsB}' (distinct=${distinctNamespaces})\n` +
        `  x-cache A='${cacheA}' B='${cacheB}' (bothMiss=${bothMiss})\n` +
        `O backend precisa expor pelo menos um destes para que o sealing seja auditável. ` +
        `Adicione \`x-cache-key\` (preferível) ou \`x-tenant-cache-namespace\` na resposta do chat.`,
    ).toBe(true);

    // ---- (P2) Corpo NUNCA pode vazar company_id do outro tenant. ----
    expect(
      bodyA.includes(TENANT_B.companyId),
      `LEAK (P2): resposta do tenant A contém company_id de B (${TENANT_B.companyId}).`,
    ).toBeFalsy();
    expect(
      bodyB.includes(TENANT_A.companyId),
      `LEAK (P2): resposta do tenant B contém company_id de A (${TENANT_A.companyId}).`,
    ).toBeFalsy();

    await ctxA.close();
    await ctxB.close();
  });

  test("B4 — busca de candidato exclusivo do tenant A retorna 0 hits para tenant B", async ({
    page,
  }) => {
    test.skip(
      !uniqueCandidateName,
      "depende de B1 ter rodado e semeado o candidato",
    );
    await loginUI(page, TENANT_B);
    const resp = await page.request.get(
      `/api/v1/candidates/search?q=${encodeURIComponent(uniqueCandidateName)}`,
    );
    expect(resp.status()).toBe(200);
    const body = (await resp.json()) as {
      results?: unknown[];
      total?: number;
    };
    const total =
      body.total ??
      (Array.isArray(body.results) ? body.results.length : 0);
    expect(
      total,
      `tenant B não pode ver candidato exclusivo '${uniqueCandidateName}' do tenant A (got ${total} hits)`,
    ).toBe(0);
  });
});
