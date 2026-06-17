import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/public-vacancies/p/:slug",
  methods: ["GET"],
  auth: false,
})
