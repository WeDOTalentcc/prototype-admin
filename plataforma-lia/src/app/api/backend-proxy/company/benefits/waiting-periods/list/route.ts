import { createProxyHandlers } from "@/lib/api/proxy-handler"

/**
 * Proxy canonical para taxonomia v2 de beneficios — periodos de carencia.
 * Backend: build_waiting_periods_response() em benefits_service.py
 */
export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/company/benefits/waiting-periods/list",
  methods: ["GET"],
  auth: true,
  backendTarget: "fastapi",
})
