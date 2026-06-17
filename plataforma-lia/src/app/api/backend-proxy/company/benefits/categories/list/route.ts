import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * Proxy canonical para taxonomia v2 de beneficios — categorias.
 * Backend: lia-agent-system/app/api/v1/company_benefits.py
 *          → build_categories_response() em benefits_service.py
 *
 * canonical-fix: single source of truth no backend. Frontend nao hardcoda.
 */
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/benefits/categories/list",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
