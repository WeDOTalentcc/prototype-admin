import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/company/global-search-settings",
  methods: ["GET", "PUT"],
  auth: true,
  backendTarget: "rails",
})
