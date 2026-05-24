import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * Proxy canonical para taxonomia v2 de beneficios — tipos de valor.
 * Backend: build_value_types_response() em benefits_service.py
 */
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/benefits/value-types/list",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
