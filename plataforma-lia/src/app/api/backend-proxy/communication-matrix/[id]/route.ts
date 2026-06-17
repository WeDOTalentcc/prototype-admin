import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/communication-matrix/:id",
  methods: ["GET", "PUT"],
  auth: true,
})
