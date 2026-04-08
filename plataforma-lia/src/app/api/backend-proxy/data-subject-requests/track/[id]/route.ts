import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET } = createProxyHandlers({
  backendPath: "/api/v1/data-subject-requests/track/:id",
  methods: ["GET"],
  auth: true,
})
