import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/portal/proposta/:id",
  methods: ["GET"],
  auth: false,
})
