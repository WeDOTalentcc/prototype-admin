import { createProxyHandlers } from "@/lib/api/proxy-handler"

export const { dynamic, GET, PUT } = createProxyHandlers({
  backendPath: "/api/v1/pii-visibility-defaults",
  methods: ["GET", "PUT"],
  backendTarget: "fastapi",
})
