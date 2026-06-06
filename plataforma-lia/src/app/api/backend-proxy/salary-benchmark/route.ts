import { createProxyHandlers } from "@/lib/api/proxy-handler"

// Benchmark salarial de mercado (D7) — fonte p/ o FALLBACK da faixa salarial
// quando NAO ha banda cadastrada da empresa pro escopo da vaga. Estimativa
// (Glassdoor/LinkedIn via Apify + fallback setorial) — sempre rotulada como
// "estimativa de mercado" no UI (proveniencia honesta, CLAUDE.md REGRA 4).
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/salary-benchmark",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
